from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Company.models import Company
from rest_framework.permissions import IsAuthenticated
from ..Serializers.manageusers import showcompaniesSerializer, userSerializer, UserRoleShowSerializer
from ..ModelsByPage.DashAdmin import UserRoles

class ManageUsersView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        users = PortalUser.objects.all()
        serializer = userSerializer(users, many=True)
        companies = Company.objects.all()
        company_serializer = showcompaniesSerializer(companies, many=True)
        uroles = UserRoles.objects.all()
        ureader = UserRoleShowSerializer(uroles, many=True)
        return Response({"companies": company_serializer.data, "users": serializer.data, "roles":ureader.data}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        pass
    def put(self, request, pk, *args, **kwargs):
        pass
    def delete(self, request, pk, *args, **kwargs):
        try:
            user = PortalUser.objects.get(id=pk)
            user.delete()
            return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)
        except PortalUser.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


        