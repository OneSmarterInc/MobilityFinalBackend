from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.requestser import VendorPlanSerializer, showOrganizations,showvendorPlanSerializer, showOnboardedSerializer
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from ..ModelsByPage.Req import VendorPlan
from OnBoard.Organization.models import Organizations
from authenticate.views import saveuserlog

class VendorPlanView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = VendorPlan.objects.filter(sub_company=pk)
            ser = showvendorPlanSerializer(obj, many=True)
            return Response({"data": ser.data}, status=status.HTTP_200_OK)
        else:
            orgs = Organizations.objects.exclude(status=False)
            org_ser = showOrganizations(orgs, many=True)
            return Response({"orgs": org_ser.data}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if VendorPlan.objects.filter(vendor=data.get("vendor"), ban=data.get("ban"), sub_company=data.get('sub_company'), plan=data.get('plan')).exists():
            return Response({"message": "Vendor plan already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        ser = VendorPlanSerializer(data=data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f"vendor plan created for account number {ser.data['ban']}")
            return Response({"message": "Vendor plan added successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Unable to add vendor plan."}, status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request, pk, *args, **kwargs):
        obj = VendorPlan.objects.filter(id=pk).first()
        if not obj:
            return Response({"message": "Vendor plan not found"}, status=status.HTTP_400_BAD_REQUEST)
        ser = VendorPlanSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f"vendor plan updated for account number {obj.ban}")
            return Response({"message": "Vendor plan updated successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Unable to update vendor plan."}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk, *args, **kwargs):
        obj = VendorPlan.objects.filter(id=pk).first()
        if not obj:
            return Response({"message": "Vendor plan not found"}, status=status.HTTP_400_BAD_REQUEST)
        ban = obj.ban
        obj.delete()
        saveuserlog(request.user, f"vendor plan of account number {ban} deleted")
        return Response({"message": "Vendor plan deleted successfully!"}, status=status.HTTP_200_OK)