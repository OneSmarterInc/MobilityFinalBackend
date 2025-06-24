from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import Permission
from OnBoard.Organization.models import Organizations
from rest_framework.permissions import IsAuthenticated
from ..ModelsByPage.Req import Requests
from ..Serializers.requestser import showRequestSerializer, showOrganizations, showUsers, RequestsSaveSerializer, showOnboardedSerializer, OrganizationShowSerializer, VendorShowSerializer, UniquePdfShowSerializer
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable
from authenticate.models import PortalUser

class RequestsView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        if pk==None:
            all_objs = Requests.objects.all()
            ser = showRequestSerializer(all_objs, many=True)
        else:
            obj = Requests.objects.get(id=pk)
            ser = showRequestSerializer(obj)
        orgs = showOrganizations(Organizations.objects.all(), many=True)
        users = showUsers(PortalUser.objects.exclude(company=None) ,many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).exclude(Entry_type="Master Account"), many=True)
        return Response({"data":ser.data,"organizations":orgs.data, "users":users.data, "bans":onboarded.data},status=status.HTTP_200_OK)
    
        
    def put(self, request,pk, *args, **kwargs):
        try:
            obj = Requests.objects.get(id=pk)
        except Requests.DoesNotExist:
            return Response({"message":"Request not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = request.data.copy() 
        data = json.loads(data) if not isinstance(data, dict) else data
        ser = RequestsSaveSerializer(obj, data=data,partial=True)
        if ser.is_valid():
            ser.save()
            return Response({"message":"Request updated successfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request,pk, *args, **kwargs):
        try:
            re = Requests.objects.get(id=pk)
            re.delete()
            return Response({"message": "Request deleted successfully!"}, status=status.HTTP_200_OK)
        except Requests.DoesNotExist:
            return Response({"message": "request does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
import json

class OnlineFormView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
       
        orgs = OrganizationShowSerializer(Organizations.objects.all(), many=True)
        vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).exclude(Entry_type="Master Account"), many=True)
        unique = UniquePdfShowSerializer(UniquePdfDataTable.objects.filter(viewuploaded=None,viewpapered=None), many=True)
        users = showUsers(PortalUser.objects.exclude(company=None) ,many=True)
        return Response({"organizations":orgs.data, "vendors":vendors.data, "bans":onboarded.data, "lines":unique.data,"users":users.data},status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        lines = data.pop("lines")
        if type(lines[0]) == str:
            lines = json.loads(lines[0])
        if 'other_documents' in data:
            other_documents = data.pop("other_documents")
        else:
            other_documents = None
        org_name = lines[0].pop('organization')
        vendor_name = lines[0].pop('vendor')
        r_type = lines[0].get('request_type')
        try:
            org = Organizations.objects.get(Organization_name=org_name)
        except Organizations.DoesNotExist:
            return Response({"organization": f"Organization with name '{org_name}' does not exist."})
        try:
            ven = Vendors.objects.get(name=vendor_name)
        except Vendors.DoesNotExist:
            return Response({"vendor": f"Vendor with name '{vendor_name}' does not exist."})
        print(lines)
        added = 0
        for line in lines:
            line['requester'] = request.user.id
            line['organization'] = org.id
            line['vendor'] = ven.id
            if other_documents:
                line['other_documents'] = other_documents[0]
            ser = RequestsSaveSerializer(data=line)
            if ser.is_valid():
                ser.save()
            else:
                print(ser.errors)
                return Response({"message":{str(ser.errors)}},status=status.HTTP_400_BAD_REQUEST)
        return Response({"message":f"{len(lines)} Lines added successfully!" if r_type=='Add New Line' else "Request added successfully!"},status=status.HTTP_200_OK)

class RequestLogsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        if pk==None:
            all_objs = Requests.objects.all()
            ser = showRequestSerializer(all_objs, many=True)
        else:
            obj = Requests.objects.get(id=pk)
            ser = showRequestSerializer(obj)
        orgs = showOrganizations(Organizations.objects.all(), many=True)
        users = showUsers(PortalUser.objects.exclude(company=None) ,many=True)

        return Response({"data":ser.data,"organizations":orgs.data, "users":users.data},status=status.HTTP_200_OK)
    
        
    def put(self, request,pk, *args, **kwargs):
        try:
            obj = Requests.objects.get(id=pk)
        except Requests.DoesNotExist:
            return Response({"message":"Request not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = request.data.copy()
        print(data)
        ser = RequestsSaveSerializer(obj, data=data,partial=True)
        if ser.is_valid():
            ser.save()
            return Response({"message":"Request updated successfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request,pk, *args, **kwargs):
        try:
            re = Requests.objects.get(id=pk)
            re.delete()
            return Response({"message": "Request deleted successfully!"}, status=status.HTTP_200_OK)
        except Requests.DoesNotExist:
            return Response({"message": "request does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
from addon import str_to_bool

class RequestExcelUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, org, *args, **kwargs):
        try:
            orgobj = Organizations.objects.get(Organization_name=org)
        except Organizations.DoesNotExist:
            return Response({"organization": f"Organization with name '{org}' does not exist."})
        
        data = request.data.copy()
        print(data)

        try:
            objects = []
            for obj in data:
                obj['organization'] = orgobj
                obj['requester'] = request.user
                if not Vendors.objects.filter(name=obj['vendor']).exists():
                    continue
                else:
                    obj['vendor'] = Vendors.objects.get(name=obj['vendor'])
                obj['delivery_verified'] = str_to_bool(obj['delivery_verified']) if 'delivery_verified' in obj else False #1
                obj['activation_verified'] = str_to_bool(obj['activation_verified']) if 'activation_verified' in obj else False #2
                obj['is_call_forwarding'] = str_to_bool(obj['is_call_forwarding']) if 'is_call_forwarding' in obj else False #3
                obj['is_susped_30_days'] = str_to_bool(obj['is_susped_30_days']) if 'is_susped_30_days' in obj else False #4
                obj['is_new_device'] = str_to_bool(obj['is_new_device']) if 'is_new_device' in obj else False #5
                obj['is_remote'] = str_to_bool(obj['is_remote']) if 'is_remote' in obj else False #6
                obj['is_insurance'] = str_to_bool(obj['is_insurance']) if 'is_insurance' in obj else False #7
                obj['is_voice_calling'] = str_to_bool(obj['is_voice_calling']) if 'is_voice_calling' in obj else False #8
                obj['is_international_plan'] = str_to_bool(obj['is_international_plan']) if 'is_international_plan' in obj else False #9
                
                objects.append(Requests(**obj))  # Convert dict to model instance

            Requests.objects.bulk_create(objects, ignore_conflicts=True)
            return Response({"message": "Excel data uploaded successfully!"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


