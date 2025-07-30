from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.requestser import VendorDeviceSerializer, showOrganizations,showVendorDeviceSerializer
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from ..ModelsByPage.Req import VendorDevice
from OnBoard.Organization.models import Organizations

class VendorDeviceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = VendorDevice.objects.filter(sub_company=pk)
            ser = showVendorDeviceSerializer(obj, many=True)
            return Response({"data":ser.data},status=status.HTTP_200_OK)
        else:
            orgs = Organizations.objects.exclude(status=False)
            org_ser = showOrganizations(orgs,many=True)
            return Response({"orgs":org_ser.data},status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        if VendorDevice.objects.filter(model=data.get("model"), sub_company=data.get("sub_company"), vendor=data.get('vendor')).exists():
            return Response({"message":"Vendor device already exists!"},status=status.HTTP_400_BAD_REQUEST)
        ser = VendorDeviceSerializer(data=data)
        if ser.is_valid():
            ser.save()
            return Response({"message":"vendor device added succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request, pk, *args, **kwargs):
        obj = VendorDevice.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"vendor device not found"},status=status.HTTP_400_BAD_REQUEST)
        ser = VendorDeviceSerializer(obj,data=request.data,partial=True)
        if ser.is_valid():
            ser.save()
            return Response({"message":"vendor device updated succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk, *args, **kwargs):
        obj = VendorDevice.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"vendor device not found"},status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response({"message":"vendor device deleted sucessfully!"},status=status.HTTP_200_OK)