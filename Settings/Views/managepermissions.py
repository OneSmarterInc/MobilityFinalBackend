
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..models import PermissionsbyCompany
from ..ser import permissionsSerializer,PermissionShowSerializer
from OnBoard.Company.models import Company
from Dashboard.ModelsByPage.DashAdmin import UserRoles
class ManagePermissionsView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, company, *args, **kwargs):
        company = Company.objects.filter(Company_name=company).first()
        if not company:
            return Response({"message":"Company not found!"},status=status.HTTP_400_BAD_REQUEST) 
        ser = PermissionShowSerializer(PermissionsbyCompany.objects.filter(company=company), many=True)
        return Response({"data":ser.data},status=status.HTTP_200_OK)

    def post(self, request, company, *args, **kwargs):
        
        company = Company.objects.filter(Company_name=company).first()

        data = request.data
        role_name = data.pop('role')
        role = UserRoles.objects.filter(name=role_name).first()
        if not role:
            return Response({"message": "User role not found!"}, status=status.HTTP_400_BAD_REQUEST)

        # Try to get existing permission record
        instance = PermissionsbyCompany.objects.filter(company=company, role=role).first()
        print(instance)

        if instance:
            # Update existing one
            ser = permissionsSerializer(instance, data=data, partial=True)
        else:
            # Create new one
            ser = permissionsSerializer(data={"company": company.id if company else None, "role": role.id, **data})

        if ser.is_valid():
            ser.save()
            return Response({"message": "User role permission updated successfully"}, status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message": "Unable to add/edit user role permissions"}, status=status.HTTP_400_BAD_REQUEST)

    
    def put(self, request, company, *args, **kwargs):
        pass