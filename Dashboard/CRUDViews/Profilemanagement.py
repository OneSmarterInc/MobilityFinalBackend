from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import Permission
from OnBoard.Organization.models import Organizations
from rest_framework.permissions import IsAuthenticated
from ..Serializers.promange import OrganizationsShowSerializer, showdesignations, showusers, ProfileSaveSerializer, ProfileShowSerializer, PermissionSerializer, ProfilePermissionSerializer
from ..ModelsByPage.DashAdmin import UserRoles
from authenticate.models import PortalUser
from ..ModelsByPage.ProfileManage import Profile

class ProfileManageView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):   
        if request.user.designation.name == "Superadmin":
            orgs = Organizations.objects.all()
        else:
            orgs = Organizations.objects.filter(company=request.user.company)
        
        ser = OrganizationsShowSerializer(orgs, many=True)
        desg = UserRoles.objects.exclude(name='Superadmin')
        desgser = showdesignations(desg, many=True)
        all_comapny_users = PortalUser.objects.exclude(company=None)
        company_users_ser = showusers(all_comapny_users, many=True)

        all_org_users = Profile.objects.all()
        org_users_ser = ProfileShowSerializer(all_org_users, many=True)
        
        return Response({"orgs": ser.data, "desg":desgser.data, "company_users":company_users_ser.data, "org_users":org_users_ser.data}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        org = data.get('organization')
        orginstance = Organizations.objects.get(id=org)
        check = Profile.objects.filter(organization=org,user=data.get('user'))
        if check:
            return Response({"message": f"User already designated as {check[0].role.name} for organization {orginstance.Organization_name}!"}, status=status.HTTP_400_BAD_REQUEST)
        ser = ProfileSaveSerializer(data=data)
        if ser.is_valid():
            ser.save()
            return Response({"message": "New User added successfully!"}, status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message": f"{str(ser.errors)}"}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request,pk, *args, **kwargs):
        org = Organizations.objects.filter(id=pk)
        if not org.exists():
            return Response({"message":"Organization not found!"}, status=status.HTTP_400_BAD_REQUEST)
        org = org[0]
        data = request.data.copy().get('contacts')
        for contact in data:
            obj = Profile.objects.get(id=contact.get('id'))
            ser = ProfileSaveSerializer(obj, data=contact, partial=True)
            if ser.is_valid():
                ser.save()
            else:
                print(ser.errors)
                return Response({"message": f"{str(ser.errors)}"}, status=status.HTTP_400_BAD_REQUEST)
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
        role = role[0]
        data = request.data.copy()
        ser = ProfileSaveSerializer(role, data=data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response({"message": f"Permission list for {role.role.name} updated successfully!"}, status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message": f"{str(ser.errors)}"}, status=status.HTTP_400_BAD_REQUEST)
        