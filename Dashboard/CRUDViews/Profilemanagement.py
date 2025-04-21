from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations
from rest_framework.permissions import IsAuthenticated
from ..Serializers.promange import OrganizationsShowSerializer, showdesignations, showusers
from ..ModelsByPage.DashAdmin import UserRoles
from authenticate.models import PortalUser

class ProfileManageView(APIView):
    permission_classes = [IsAuthenticated]
    def __init__(self):
        self.users = None
    def get(self, request, *args, **kwargs):   
        if request.user.designation.name == "Superadmin":
            orgs = Organizations.objects.all()
        else:
            orgs = Organizations.objects.filter(company=request.user.company)
        desg = UserRoles.objects.exclude(name='Superadmin')
        action = request.GET.get('action')
        org = request.GET.get('org')
        if action == 'get-all-users-by-org' and org :
            all_users = PortalUser.objects.filter(company=org)
            orgser = showusers(all_users, many=True)
            self.users = orgser.data
        desgser = showdesignations(desg, many=True)
        ser = OrganizationsShowSerializer(orgs, many=True)
        return Response({"orgs": ser.data, "desg":desgser.data, "users":self.users}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        return Response({"message": "Post"}, status=status.HTTP_200_OK)
    def put(self, request,pk, *args, **kwargs):
        return Response({"message": "Put"}, status=status.HTTP_200_OK)
    def delete(self, request, pk, *args, **kwargs):
        return Response({"message": "Delete"}, status=status.HTTP_200_OK)