from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.cat import catserializer
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from ..ModelsByPage.Req import Device
from OnBoard.Organization.models import Organizations
from ..Serializers.requestser import devicesSerializer, showdevicesSerializer,showOrganizations
class DevicesView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = Device.objects.filter(sub_company=pk)
            ser = showdevicesSerializer(obj,many=True)
            return Response({"data":ser.data},status=status.HTTP_200_OK)
        else:
            orgs = Organizations.objects.filter(company=request.user.company) if request.user.company else Organizations.objects.all()
            org_ser = showOrganizations(orgs,many=True)
            return Response({"orgs":org_ser.data},status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):

        data = request.data.copy()
        print(data)
        if Device.objects.filter(model=data.get("model"), sub_company=data.get("sub_company"), device_type=data.get('device_type')).exists():
            return Response({"message":"Device already exists!"},status=status.HTTP_400_BAD_REQUEST)
        ser = devicesSerializer(data=data)
        if ser.is_valid():
            ser.save()
            return Response({"message":"Device added succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, pk, *args, **kwargs):
        obj = Device.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"Device not found"},status=status.HTTP_400_BAD_REQUEST)
        ser = devicesSerializer(obj,data=request.data,partial=True)
        if ser.is_valid():
            ser.save()
            return Response({"message":"Device updated succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk, *args, **kwargs):
        obj = Device.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"Device not found"},status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response({"message":"Device deleted sucessfully!"},status=status.HTTP_200_OK)
    
# class ApprovedDevicesView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, pk=None, *args, **kwargs):
#         if pk:
#             obj = ApprovedDevice.objects.filter(id=pk).first()
#             ser = showapproveddevicesSerializer(obj)
#         else:
#             objs = ApprovedDevice.objects.all()
#             ser = showapproveddevicesSerializer(objs,many=True)
#         return Response({"data":ser.data},status=status.HTTP_200_OK)
#     def post(self, request, *args, **kwargs):
#         data = request.data.copy()
#         ser = approveddevicesSerializer(data=data)
#         if ser.is_valid():
#             ser.save()
#             return Response({"message":"Device added succesfully!"},status=status.HTTP_200_OK)
#         else:
#             return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
#     def put(self, request, pk, *args, **kwargs):
#         obj = ApprovedDevice.objects.filter(id=pk).first()
#         if not obj:
#             return Response({"message":"Device not found"},status=status.HTTP_400_BAD_REQUEST)
#         ser = approveddevicesSerializer(obj,data=request.data,partial=True)
#         if ser.is_valid():
#             ser.save()
#             return Response({"message":"Device updated succesfully!"},status=status.HTTP_200_OK)
#         else:
#             return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
#     def delete(self, request, pk, *args, **kwargs):
#         obj = ApprovedDevice.objects.filter(id=pk).first()
#         if not obj:
#             return Response({"message":"Device not found"},status=status.HTTP_400_BAD_REQUEST)
#         obj.delete()
#         return Response({"message":"Device deleted sucessfully!"},status=status.HTTP_200_OK)