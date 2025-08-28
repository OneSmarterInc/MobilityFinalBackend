from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Organization.models import Organizations
from rest_framework.permissions import IsAuthenticated
from Dashboard.ModelsByPage.DashAdmin import Vendors
from ..Serializers.ven import VendorsSerializer, OrganizationListSerializer
from authenticate.views import saveuserlog

class VendorsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        if request.user.designation.name == "Superadmin":
            orgs = Organizations.objects.all()
        else:
            orgs = Organizations.objects.filter(company=request.user.company)
        if pk:
            ven = Vendors.objects.filter(name=pk)[0]
            serializer = VendorsSerializer(ven)
        else:
            ven = Vendors.objects.all()
            serializer = VendorsSerializer(ven, many=True)
        orgser = OrganizationListSerializer(orgs, many=True)
        return Response({"data": serializer.data, "orgs": orgser.data},status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        pass
    def put(self, request, pk, *args, **kwargs):
        vendor = Vendors.objects.filter(id=pk)
        org = request.data.pop('organization_name', None)
        org = Organizations.objects.get(Organization_name=org)
        if request.data['action'] == 'add-favorite':
            org.favorite_vendors.add(vendor.first())
            org.save()
        elif request.data['action'] == 'remove-favorite':
            print(vendor)
            org.favorite_vendors.remove(vendor.first())
            org.save()
            saveuserlog(request.user, f"vendor {vendor.first().name} updated successfully!")
        return Response({"message":"vendor updated successfully!"})
    def delete(self, request, pk, *args, **kwargs):
        pass