from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import UserRoles
from ...Serializers.AdminPage import UserRoleSaveSerializer, UserRoleShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog

from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations

class UserRoleView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk=None):
        if pk:
            user_role = UserRoles.objects.get(name=pk)
            ser = UserRoleShowSerializer(user_role)
            return Response({"data":ser.data}, status=status.HTTP_200_OK)
        else:
            user_roles = UserRoles.objects.exclude(id=request.user.designation.id).filter(company=request.user.company, organization=request.user.organization)
            print(user_roles)
            ser = UserRoleShowSerializer(user_roles, many=True)
            return Response({"data":ser.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        if UserRoles.objects.filter(name=request.data["name"]).exists():
            return Response({"message": "User role with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            data=request.data
            company = data.pop('company')
            companyObj = Company.objects.filter(Company_name=company).first()
            companyID = companyObj.id if companyObj else None
            organization = data.pop('organization')
            orgObj = Organizations.objects.filter(Organization_name=organization).first()
            orgID = orgObj.id if orgObj else None
            ser = UserRoleSaveSerializer(data={"company":companyID, "organization":orgID, **data})
            if ser.is_valid():
                ser.save()
                saveuserlog(request.user, f'new user role created {ser.data["name"]}')
                return Response({"message":"new user role created successfully!", "data":ser.data}, status=status.HTTP_201_CREATED)
            return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, pk):
        try:
            user_role = UserRoles.objects.get(name=pk)
        except UserRoles.DoesNotExist:
            return Response({"message": "User role does not exist!"}, status=status.HTTP_404_NOT_FOUND)
        ser = UserRoleSaveSerializer(user_role, data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f'user role updated {ser.data["name"]}') 
            return Response({"message":"user role updated successfully!", "data":ser.data}, status=status.HTTP_200_OK)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            user_role = UserRoles.objects.get(name=pk)
            user_role.delete()
            saveuserlog(request.user, f'user role deleted {pk}')
            return Response({"message": "User role deleted successfully!"}, status=status.HTTP_200_OK)
        except UserRoles.DoesNotExist:
            return Response({"message": "User role does not exist"}, status=status.HTTP_400_BAD_REQUEST)
    

