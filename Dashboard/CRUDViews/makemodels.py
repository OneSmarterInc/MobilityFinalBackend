from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.requestser import MakeModelSerializer, showOrganizations,showMakeModelSerializer
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from ..ModelsByPage.Req import MakeModel
from OnBoard.Organization.models import Organizations
from authenticate.views import saveuserlog
from Batch.views import create_notification
class MakeModelView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = MakeModel.objects.filter(sub_company=pk)
            ser = showMakeModelSerializer(obj, many=True)
            return Response({"data":ser.data},status=status.HTTP_200_OK)
        else:
            orgs = Organizations.objects.exclude(status=False)
            org_ser = showOrganizations(orgs,many=True)
            return Response({"orgs":org_ser.data},status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        ser = MakeModelSerializer(data=data)
        if ser.is_valid():
            ser.save()
            data = ser.data
            saveuserlog(request.user, f"New model {data['name']} of device type {data['device_type']} added.")
            create_notification(request.user, f"New model {data['name']} of device type {data['device_type']} added.",request.user.company)
            return Response({"message":"Model added succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":"Unable to add new model."},status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, pk, *args, **kwargs):
        obj = MakeModel.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"Model not found"},status=status.HTTP_400_BAD_REQUEST)
        ser = MakeModelSerializer(obj,data=request.data,partial=True)
        if ser.is_valid():
            ser.save()
            data = ser.data
            saveuserlog(request.user, f"Model {data['name']} of device type {data['device_type']} updated.")
            create_notification(request.user, f"Model {data['name']} of device type {data['device_type']} updated.",request.user.company)
            return Response({"message":"Model updated succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":"Unable to update model."},status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk, *args, **kwargs):
        obj = MakeModel.objects.filter(id=pk).first()
        name = obj.name
        dtype = obj.device_type
        if not obj:
            saveuserlog(request.user, f"Model {name} of device type {dtype} deleted.")
            create_notification(request.user, f"Model {name} of device type {dtype} deleted.",request.user.company)
            return Response({"message":"Model not found"},status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response({"message":"Model deleted sucessfully!"},status=status.HTTP_200_OK)
