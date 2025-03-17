from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations
from rest_framework.permissions import IsAuthenticated
from ..Serializers.promange import OrganizationsShowSerializer
from ..ModelsByPage.DashAdmin import UserRoles

class ProfileManageView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):   
        if request.user.designation.name == "Superadmin":
            orgs = Organizations.objects.all()
        else:
            orgs = Organizations.objects.filter(company=request.user.company)
        ser = OrganizationsShowSerializer(orgs, many=True)
        return Response({"orgs": ser.data}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        return Response({"message": "Post"}, status=status.HTTP_200_OK)
    def put(self, request,pk, *args, **kwargs):
        return Response({"message": "Put"}, status=status.HTTP_200_OK)
    def delete(self, request, pk, *args, **kwargs):
        return Response({"message": "Delete"}, status=status.HTTP_200_OK)