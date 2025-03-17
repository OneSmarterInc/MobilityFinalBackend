from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Company.models import Company
from rest_framework.permissions import IsAuthenticated
from ..Serializers.manageusers import showcompaniesSerializer, userSerializer, UserRoleShowSerializer
from ..ModelsByPage.DashAdmin import UserRoles

class ProfileManageView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        return Response({"message": "Get"}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        return Response({"message": "Post"}, status=status.HTTP_200_OK)
    def put(self, request,pk, *args, **kwargs):
        return Response({"message": "Put"}, status=status.HTTP_200_OK)
    def delete(self, request, pk, *args, **kwargs):
        return Response({"message": "Delete"}, status=status.HTTP_200_OK)