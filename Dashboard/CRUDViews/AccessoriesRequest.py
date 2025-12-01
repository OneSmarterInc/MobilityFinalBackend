from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

from rest_framework import status
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from ..ModelsByPage.Req import AccessoriesRequest, CostCenters
from ..Serializers.requestser import SaveaccessoriesRequestSer, ShowaccessoriesRequestSer
from authenticate.views import saveuserlog
from django.forms.models import model_to_dict
from Batch.views import create_notification
from ..ModelsByPage.DashAdmin import Vendors
from OnBoard.Organization.models import Organizations

import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

class AccessoryRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,pk=None, *args, **kwargs):
        if pk:
            obj = AccessoriesRequest.objects.filter(id=pk).first()
            ser = ShowaccessoriesRequestSer(obj)
        else:
            company = request.user.company
            organization = request.user.organization
            if "admin" not in request.user.designation.name.lower():
                all_objs = AccessoriesRequest.objects.filter(requester=request.user)
            else:
                if company and not organization:
                    all_objs = AccessoriesRequest.objects.filter(
                        Q(status="Approved") | Q(requester=request.user)
                    )
                elif company and organization:
                    all_objs = AccessoriesRequest.objects.filter(organization=request.user.organization)
                else:
                    all_objs = AccessoriesRequest.objects.filter(requester=request.user)
            ser = ShowaccessoriesRequestSer(all_objs, many=True)
        return Response({"data":ser.data},status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        print(data)
        org = data.pop("organization",None)
        vendor = data.pop("vendor",None)
        ban = data.get("ban", None)
        wn = data.get("line_of_service", None)
        org = Organizations.objects.filter(Organization_name=org).first()
        vendor = Vendors.objects.filter(name=vendor).first()

        print(org, vendor, ban, wn)
        if not (org or vendor or ban or wn):
            return Response({"message":"Some fields are neccessary to raise a request"},status=status.HTTP_400_BAD_REQUEST)
        
        data["organization"] = org.id
        data["vendor"] = vendor.id
        data["requester"] = request.user.id

        ser = SaveaccessoriesRequestSer(data=data)
        if ser.is_valid():
            ser.save()
            data = ser.data
            saveuserlog(request.user, f"{data["request_type"]} Request for wireless number {data["line_of_service"]} created.")
            create_notification(request.user, f"{data["request_type"]} Request for wireless number {data["line_of_service"]} created.",request.user.company)
            return Response({"message":"Your request is raised successfully"},status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message":"Unable to raise requests"},status=status.HTTP_400_BAD_REQUEST)


    def put(self, request,pk, *args, **kwargs):
        try:
            obj = AccessoriesRequest.objects.get(id=pk)
        except AccessoriesRequest.DoesNotExist:
            return Response({"message":"Request not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":"Internal Server Error!"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = request.data.copy() 
        data = json.loads(data) if not isinstance(data, dict) else data
        ser = SaveaccessoriesRequestSer(obj, data=data,partial=True)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f"{data["request_type"]} Request for wireless number {data["line_of_service"]} updated.")
            create_notification(request.user, f"{data["request_type"]} Request for wireless number {data["line_of_service"]} updated.",request.user.company)
            return Response({"message":"Request updated successfully!"},status=status.HTTP_200_OK)
        
        else:
            print(ser.errors)
            return Response({"message":"Unable to update request!"},status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request,pk, *args, **kwargs):
        try:
            re = AccessoriesRequest.objects.filter(id=pk).first()
            R_type = re.request_type
            line = re.line_of_service
            re.delete()
            saveuserlog(request.user, f"{R_type} Request for wireless number {line} deleted.")
            create_notification(request.user, f"{R_type} Request for wireless number {line} deleted.",request.user.company)
            return Response({"message": "Request deleted successfully!"}, status=status.HTTP_200_OK)
        except AccessoriesRequest.DoesNotExist:
            return Response({"message": "request does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"message":"Unable to delete request."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_status(request,pk):
    obj = AccessoriesRequest.objects.filter(id=pk).first()
    if not obj:
        return Response({"message": "request does not exist"}, status=status.HTTP_400_BAD_REQUEST) 
    data = request.data
    print(data)
    try:
        s_type = data.get("status_type")
        updated = data.get("newStatus")
        if s_type == "status":
            obj.status = updated
        elif s_type == "authority_status":
            obj.authority_status = updated
        obj.save()
        return Response({"message":"Request status updated successfully!"},status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message":"Unable to update request status."}, status=status.HTTP_400_BAD_REQUEST)
    
def check_true(var):
    if not var: return False
    elif isinstance(var,bool): return var
    else: return str(var).lower() in ("yes","true")

import pandas as pd
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_bulk_accessories_request(request, org):
    org = Organizations.objects.filter(Organization_name=org).first()
    if not org:
        return Response({"message":"Organization not found!"},status=status.HTTP_400_BAD_REQUEST)
    requester = request.user
    data = request.data
    mapping = data.get("mapping")
    mapped_data = data.get("data")
    if not mapping and mapped_data:
        return Response({"message":"Mapping and mapped data are necessary!"},status=status.HTTP_400_BAD_REQUEST)
    
    vendor = mapping.pop('vendor')
    ban = mapping.pop('ban')
    
    request_type = mapping.pop('request_type')
    vendor = Vendors.objects.get(name__iexact=vendor)
    if not (vendor or ban or request_type):
        return Response({"message":"Follwing fields are important: vendor,ban,request type!"},status=status.HTTP_400_BAD_REQUEST)
    final_objects = []
    for item in mapped_data:
        other_specs = {}
        lst = item.keys()
        if item.get("device_type",None): other_specs["type"] = item.pop("device_type")
        if item.get("device_color",None): other_specs["color"] = item.pop("device_color")
        if item.get("device_storage",None): other_specs["storage"] = item.pop("device_storage")
        model=item.pop('model') if 'model' in lst else None
        manufacturer=item.pop('device') if 'device' in lst else None
        is_remote=check_true(item.pop("is_remote")) if 'is_remote' in lst else False
        obj = AccessoriesRequest(
            organization=org,
            request_type=request_type,
            requester=requester,
            vendor=vendor,
            ban=ban,
            name=model,
            manufacturer=manufacturer,
            other_specifications=other_specs,
            is_remote=is_remote,
            **item
        )

        final_objects.append(obj)

    AccessoriesRequest.objects.bulk_create(final_objects)
    
    return Response({"message":"Excel uploaded successfully!"},status=status.HTTP_200_OK)