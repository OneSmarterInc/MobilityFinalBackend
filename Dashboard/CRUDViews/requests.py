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
from ..Serializers.requestser import showRequestSerializer, showOrganizations, showUsers, RequestsSaveSerializer, showOnboardedSerializer, OrganizationShowSerializer, VendorShowSerializer, UniquePdfShowSerializer, AddusertoPortalSerializer, AddusertoProfileSerializer
from Dashboard.ModelsByPage.DashAdmin import Vendors
from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable
from authenticate.models import PortalUser
from Dashboard.ModelsByPage.ProfileManage import Profile
from authenticate.views import saveuserlog

class RequestsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        if pk is None:
            all_objs = Requests.objects.all().order_by('-created')
            ser = showRequestSerializer(all_objs, many=True)
        else:
            obj = Requests.objects.get(id=pk)
            ser = showRequestSerializer(obj)
        orgs = showOrganizations(Organizations.objects.filter(company=request.user.company) if request.user.company else Organizations.objects.all(), many=True)
        users = showUsers(PortalUser.objects.exclude(company=None) ,many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).exclude(Entry_type="Master Account"), many=True)
        return Response({"data":ser.data,"organizations":orgs.data, "users":users.data, "bans":onboarded.data},status=status.HTTP_200_OK)
    
        
    def put(self, request,pk, *args, **kwargs):
        try:
            obj = Requests.objects.get(id=pk)
        except Requests.DoesNotExist:
            return Response({"message":"Request not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":"Internal Server Error!"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = request.data.copy() 
        data = json.loads(data) if not isinstance(data, dict) else data
        ser = RequestsSaveSerializer(obj, data=data,partial=True)
        if ser.is_valid():
            ser.save()
            data = ser.data
            saveuserlog(request.user, f"Request {data['request_type']} updated.")
            return Response({"message":"Request updated successfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":"Unable to update request."},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request,pk, *args, **kwargs):
        try:
            re = Requests.objects.filter(id=pk).first()
            line = re.mobile
            re.delete()
            saveuserlog(request.user, f"Request {re.request_type}  deleted.")
            return Response({"message": "Request deleted successfully!"}, status=status.HTTP_200_OK)
        except Requests.DoesNotExist:
            return Response({"message": "request does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":"Unable to delete request."}, status=status.HTTP_400_BAD_REQUEST)
    
import json

class OnlineFormView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        
        all_orgs = Organizations.objects.filter(company=request.user.company) if request.user.company else Organizations.objects.all()
        orgs = OrganizationShowSerializer(all_orgs, many=True)
        vendors = VendorShowSerializer(Vendors.objects.all(), many=True)
        onboarded = showOnboardedSerializer(BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).exclude(Entry_type="Master Account"), many=True)
        unique = UniquePdfShowSerializer(UniquePdfDataTable.objects.filter(viewuploaded=None,viewpapered=None), many=True)
        profile_users = Profile.objects.filter(organization__in=all_orgs).select_related("user")
        print(profile_users)
        users = [p.user for p in profile_users if p.user.company is not None]
        users_data = showUsers(users, many=True)
        return Response({"organizations":orgs.data, "vendors":vendors.data, "bans":onboarded.data, "lines":unique.data,"users":users_data.data},status=status.HTTP_200_OK)
    
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
        added = 0
        for line in lines:
            request_type = line.get("request_type")
            
            line['requester'] = request.user.id
            line['organization'] = org.id
            line['vendor'] = ven.id
            if other_documents:
                line['other_documents'] = other_documents[0]
            ser = RequestsSaveSerializer(data=line)
            if ser.is_valid():
                ser.save()
                data = request.data
                saveuserlog(request.user, f"request {r_type} created for organization {org_name} and line {line['mobile']}") 
            else:
                print(ser.errors)
                return Response({"message":"Unable to create request"},status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message":f"Request to add {len(lines)} Line/s created successfully!" if r_type=='Add New Line' else "Request created successfully!"},status=status.HTTP_200_OK)

class RequestLogsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        if pk==None:
            all_objs = Requests.objects.all().order_by('-created')
            ser = showRequestSerializer(all_objs, many=True)
        else:
            obj = Requests.objects.get(id=pk)
            ser = showRequestSerializer(obj)
        all_orgs = Organizations.objects.filter(company=request.user.company) if request.user.company else Organizations.objects.all()
        orgs = showOrganizations(all_orgs, many=True)
        users = showUsers(PortalUser.objects.exclude(company=None) ,many=True)

        return Response({"data":ser.data,"organizations":orgs.data, "users":users.data},status=status.HTTP_200_OK)
    
        
    def put(self, request,pk, *args, **kwargs):
        try:
            obj = Requests.objects.get(id=pk)
        except Requests.DoesNotExist:
            return Response({"message":"Request not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":"Internal Server Error!"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = request.data.copy()
        org = obj.organization.Organization_name
        ser = RequestsSaveSerializer(obj, data=data,partial=True)
        if ser.is_valid():
            ser.save()
            data = ser.data
            saveuserlog(request.user, f"request {obj.request_type} updated for organization {org} and line {obj.mobile}")
            return Response({"message":"Request updated successfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":"Unable to update request."},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request,pk, *args, **kwargs):
        try:
            re = Requests.objects.filter(id=pk).first()
            org = re.organization.Organization_name
            rt = re.request_type
            mobile = re.mobile
            re.delete()
            saveuserlog(request.user, f"request {rt} deleted for organization {org} and line {obj.mobile}")
            return Response({"message": "Request deleted successfully!"}, status=status.HTTP_200_OK)
        except Requests.DoesNotExist:
            return Response({"message": "request does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":"Unable to delete request."}, status=status.HTTP_400_BAD_REQUEST)
        
from addon import str_to_bool

class RequestExcelUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, org, *args, **kwargs):
        try:
            orgobj = Organizations.objects.get(Organization_name=org)
        except Organizations.DoesNotExist:
            return Response({"organization": f"Organization with name '{org}' does not exist."})
        
        data = request.data.copy()

        try:
            for obj in data:
                obj['organization'] = orgobj
                obj['requester'] = request.user
                if not Vendors.objects.filter(name=obj['vendor']).exists():
                    continue
                else:
                    obj['vendor'] = Vendors.objects.get(name=obj['vendor'])
                
                obj['delivery_verified'] = str_to_bool(obj.get('delivery_verified', False))  # #1
                obj['activation_verified'] = str_to_bool(obj.get('activation_verified', False))  # #2
                obj['is_call_forwarding'] = str_to_bool(obj.get('is_call_forwarding', False))  # #3
                obj['is_susped_30_days'] = str_to_bool(obj.get('is_susped_30_days', False))  # #4
                obj['is_new_device'] = str_to_bool(obj.get('is_new_device', False))  # #5
                obj['is_remote'] = str_to_bool(obj.get('is_remote', False))  # #6
                obj['is_insurance'] = str_to_bool(obj.get('is_insurance', False))  # #7
                obj['is_voice_calling'] = str_to_bool(obj.get('is_voice_calling', False))  # #8
                obj['is_international_plan'] = str_to_bool(obj.get('is_international_plan', False))  # #9
                
                instance = Requests(**obj)
                instance.save()  # Save individually to trigger signals or validations
            saveuserlog(request.user, f"Requests in bulk for organization {org} created successfully.")
            return Response({"message": "Excel data uploaded successfully!"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({"message": "Unable to create bulk requests."}, status=status.HTTP_400_BAD_REQUEST)

from Dashboard.ModelsByPage.DashAdmin import UserRoles, Vendors
from authenticate.models import PortalUser

from ..Serializers.promange import ProfileSaveSerializer
class RequestUsersExcelUploadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org, *args, **kwargs):
        errorBuffer = {}
        orgobj = Organizations.objects.filter(id=org).first()
            
        if not orgobj:
            return Response({"message": f"Organization with name '{org}' does not exist."},status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        print(data)

        for obj in data:
            vendor = obj.get('vendor')
            vendor_ids = []
            role = obj.get('user_role')
            email = obj.get('contact_email')
            phone = obj.get('contact_phone')
            username = obj.get('user_name')
            fn = obj.get('first_name')
            ln = obj.get('last_name')

            

            roleObj = UserRoles.objects.filter(name=role).first()
            if not roleObj:
                roleObj = UserRoles.objects.create(name=role)
            else:
                roleObj = roleObj
            
            
            if isinstance(vendor, list):
                # vendor is a list → filter only those that exist
                existing_vendors = Vendors.objects.filter(name__in=vendor)
                vendor_ids = list(existing_vendors.values_list('id', flat=True))
            else:
                # vendor is a single string → check one
                vendorObj = Vendors.objects.filter(name=vendor).first()
                if vendorObj:
                    vendor_ids = [vendorObj.id]
                
            PortalDict = {
                "company": orgobj.company.id, 
                "email": email,
                "first_name":fn,
                "last_name":ln,
                "username":str(email).split("@")[0],
                "phone_number":phone,
                "designation":roleObj.id,
                "password":1234,
            }
            print(PortalDict)
            portalobj = PortalUser.objects.filter(email=email)
            if not portalobj.exists():
                portalser = AddusertoPortalSerializer(data=PortalDict)
                if portalser.is_valid():
                    portalser.save()
                else:
                    print(portalser.errors)
            else: 
                portalser = AddusertoPortalSerializer(portalobj.first())
            ProfileDict = {
                "user":portalser.data.get('id'),
                "organization":orgobj.id,
                "role":roleObj.id,
                "vendors": vendor_ids,
                "email":email,
                "phone":phone,
            }
            print(ProfileDict)
            check = Profile.objects.filter(email=email)
            if check.exists():
                proobj = check.first()
                ser = ProfileSaveSerializer(proobj, data=ProfileDict, partial=True)
                if ser.is_valid():
                    ser.save()
                else:
                    print(ser.errors)
            profileser = AddusertoProfileSerializer(data=ProfileDict)
            if profileser.is_valid():
                profileser.save()
            else:
                print("errors==",profileser.errors)
                continue
            print(profileser.data)
        print(errorBuffer)
        saveuserlog(request.user, f"Profile users in bulk for organization {orgobj.Organization_name} created successfully.")
        return Response({"message":"Bulk users created successfully!"},status=status.HTTP_200_OK)

            

            


        
from ..ModelsByPage.Req import TrackingInfo
from ..Serializers.requestser import showtrackinfoSerializer,trackinfoSerializer
class TrackingInfoView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = TrackingInfo.objects.filter(request=pk)
            ser = showtrackinfoSerializer(obj,many=True)
            return Response({"data":ser.data},status=status.HTTP_200_OK)
        else:
            return Response({"message":"Request Id required"},status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, *args, **kwargs):
        obj = TrackingInfo.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"Tracking Information  not found"},status=status.HTTP_400_BAD_REQUEST)
        ser = trackinfoSerializer(obj,data=request.data,partial=True)
        if ser.is_valid():
            ser.save()
            data = ser.data
            saveuserlog(request.user, f"Tracking info for request {data['mobile']} updated.")
            return Response({"message":"Tracking Information  updated succesfully!","data":ser.data},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk, *args, **kwargs):
        obj = TrackingInfo.objects.filter(id=pk).first()
        line = obj.mobile
        if not obj:
            return Response({"message":"Tracking Information  not found"},status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        saveuserlog(request.user, f"Tracking info for request {line} updated.")
        return Response({"message":"Tracking Information  deleted sucessfully!"},status=status.HTTP_200_OK)
        
from ..Serializers.requestser import PhoneShowSerializer

class UniqueLineView(APIView):
    def get(self,request, phone, *args, **kwargs):
        if not phone:
            return Response({"message":"Wireles number required!"},status=status.HTTP_400_BAD_REQUEST)
        
        sc = request.GET.get('sub_company')
        ven = request.GET.get('vendor')
        ban = request.GET.get('ban')

        line = UniquePdfDataTable.objects.filter(viewpapered=None,viewuploaded=None).filter(sub_company=sc, vendor=ven, account_number=ban, wireless_number=phone).first()
        if not line:
            return Response({"message":f"Line {phone} not found!"},status=status.HTTP_400_BAD_REQUEST)
        ser = PhoneShowSerializer(line)
        return Response({"data":ser.data},status=status.HTTP_200_OK)