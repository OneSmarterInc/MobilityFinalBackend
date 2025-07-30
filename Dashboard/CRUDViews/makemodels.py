from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.requestser import MakeModelSerializer, showOrganizations,showMakeModelSerializer
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from ..ModelsByPage.Req import MakeModel
from OnBoard.Organization.models import Organizations


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
            return Response({"message":"Model added succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, pk, *args, **kwargs):
        obj = MakeModel.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"Model not found"},status=status.HTTP_400_BAD_REQUEST)
        ser = MakeModelSerializer(obj,data=request.data,partial=True)
        if ser.is_valid():
            ser.save()
            return Response({"message":"Model updated succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk, *args, **kwargs):
        obj = MakeModel.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"Model not found"},status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response({"message":"Model deleted sucessfully!"},status=status.HTTP_200_OK)
