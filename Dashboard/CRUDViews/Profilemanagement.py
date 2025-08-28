from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import Permission
from OnBoard.Organization.models import Organizations
from rest_framework.permissions import IsAuthenticated
from ..Serializers.promange import OrganizationsShowSerializer, showdesignations, showusers, ProfileSaveSerializer, ProfileShowSerializer, PermissionSerializer, ProfilePermissionSerializer,GetUserbyOrgSerializer
from ..ModelsByPage.DashAdmin import UserRoles
from authenticate.models import PortalUser
from ..ModelsByPage.ProfileManage import Profile
from authenticate.views import saveuserlog

class GetUserbyOrgView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request,org, *args, **kwargs):
        if not org:
            return Response({"message": f"Organization required!"}, status=status.HTTP_400_BAD_REQUEST)
        objs = Profile.objects.filter(organization=org)
        ser = GetUserbyOrgSerializer(objs,many=True)
        return Response({"data": ser.data}, status=status.HTTP_200_OK)
        
class ProfileManageView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):   
        if request.user.designation.name == "Superadmin":
            orgs = Organizations.objects.all()
        else:
            orgs = Organizations.objects.filter(company=request.user.company)
        
        ser = OrganizationsShowSerializer(orgs, many=True)
        desg = UserRoles.objects.exclude(id__in=(1,3))
        desgser = showdesignations(desg, many=True)
        all_comapny_users = PortalUser.objects.exclude(company=None).exclude(designation__in=(1,3))
        company_users_ser = showusers(all_comapny_users, many=True)

        all_org_users = Profile.objects.exclude(organization=None)
        org_users_ser = ProfileShowSerializer(all_org_users, many=True)
        
        return Response({"orgs": ser.data, "desg":desgser.data, "company_users":company_users_ser.data, "org_users":org_users_ser.data}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        org = data.get('organization')
        orginstance = Organizations.objects.filter(id=org).first()
        if not orginstance:
            return  Response({"message": f"Organization not found"}, status=status.HTTP_400_BAD_REQUEST)
        check = Profile.objects.filter(organization=org,user=data.get('user'))
        if check:
            obj = check.first()
            ser = ProfileSaveSerializer(obj, data=data, partial=True)
            if ser.is_valid():
                ser.save()
                saveuserlog(request.user, f"user profile {obj.email} updated.")
                return Response({"message": "Profile updated successfully!"}, status=status.HTTP_200_OK)
            else:
                print(ser.errors)
                return Response({"message": f"Unable to update profile"}, status=status.HTTP_400_BAD_REQUEST)
        ser = ProfileSaveSerializer(data=data)
        if ser.is_valid():
            ser.save()
            data = ser.data
            saveuserlog(request.user, f"new user profile for {data['email']} created.")
            return Response({"message": "New User added successfully!"}, status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message": "Unable to create new profile"}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request,pk, *args, **kwargs):
        org = Organizations.objects.filter(id=pk)
        if not org.exists():
            return Response({"message":"Organization not found!"}, status=status.HTTP_400_BAD_REQUEST)
        org = org[0]
        data = request.data.copy().get('contacts')
        for contact in data:
            obj = Profile.objects.filter(id=contact.get('id')).first()
            if not obj:
                continue
            ser = ProfileSaveSerializer(obj, data=contact, partial=True)
            if ser.is_valid():
                ser.save()
            else:
                print(ser.errors)
                return Response({"message": "Unable to update profile."}, status=status.HTTP_400_BAD_REQUEST)
        saveuserlog(request.user, f"user profile {obj.email} updated.")
        return Response({"message": f"Contact list for organization {org.Organization_name} updated successfully!"}, status=status.HTTP_200_OK)
    def delete(self, request, pk, *args, **kwargs):
        return Response({"message": "Delete"}, status=status.HTTP_200_OK)
    
class ProfilePermissionsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk, *args, **kwargs):   
        all_permissions = PermissionSerializer(Permission.objects.all(), many=True)
        obj_permissions = ProfilePermissionSerializer(Profile.objects.get(id=pk))
        return Response({"allpermissions":all_permissions.data, "data":obj_permissions.data},status=status.HTTP_200_OK)
    def put(self, request,pk, *args, **kwargs):
        role = Profile.objects.filter(id=pk)
        if not role.exists():
            return Response({"message":"UserRole not found!"}, status=status.HTTP_400_BAD_REQUEST)
        role = role.first()
        data = request.data.copy()
        ser = ProfileSaveSerializer(role, data=data, partial=True)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f"permissions for {role.email} updated.")
            return Response({"message": f"Permission list for {role.role.name} updated successfully!"}, status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message": "Unable to update permissions."}, status=status.HTTP_400_BAD_REQUEST)
        
class ProfileUpdateView(APIView):
    # permission_classes = [IsAuthenticated]
    def put(self, request,pk, *args, **kwargs):   
        obj = Profile.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"Profile not found!"}, status=status.HTTP_400_BAD_REQUEST) 
        
        ser = ProfileSaveSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f"user profile {obj.email} updated.")
            return Response({"message": "Profile updated successfully!"}, status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message": f"Unable to update profile"}, status=status.HTTP_400_BAD_REQUEST)
