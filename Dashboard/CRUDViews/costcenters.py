from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.cat import catserializer
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from ..ModelsByPage.Req import Device
from OnBoard.Organization.models import Organizations

from ..Serializers.requestser import devicesSerializer, showdevicesSerializer, showOrganizations
from ..ModelsByPage.Req import CostCenters
from ..Serializers.requestser import CostCentersSaveSerializer, CostCentersShowSerializer
from Dashboard.ModelsByPage.DashAdmin import Vendors
from authenticate.views import saveuserlog

class CostCentersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,org, pk=None, *args, **kwargs):
        org = Organizations.objects.filter(Organization_name=org).first()
        if not org:
            return Response({"message":"Sub company not found!"},status=status.HTTP_400_BAD_REQUEST)
        if pk:
            obj = CostCenters.objects.filter(sub_company=org.id).filter(id=pk).first()
            ser = CostCentersShowSerializer(obj)
        else:
            objs = CostCenters.objects.filter(sub_company=org.id)
            ser = CostCentersShowSerializer(objs, many=True)
        return Response({"data": ser.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        try: data['sub_company'] = int(data['sub_company'])
        except : data['sub_company'] = Organizations.objects.filter(Organization_name=data['sub_company']).first().id

        try: data['vendor'] = int(data['vendor'])
        except : data['vendor'] = Vendors.objects.filter(name=data['vendor']).first().id

        if CostCenters.objects.filter(sub_company=data['sub_company'], vendor=data['vendor'], ban=data['ban'], cost_center=data['cost_center']).exists():
            return Response({"message": "Cost Center already exists for this ban."}, status=status.HTTP_400_BAD_REQUEST)
        ser = CostCentersSaveSerializer(data=data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f"Cost Center added for account {data['ban']}")
            return Response({"message": "Cost Center added successfully!"}, status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message": "unable to add cost center."}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, *args, **kwargs):
        obj = CostCenters.objects.filter(id=pk).first()
        if not obj:
            return Response({"message": "Cost Center not found"}, status=status.HTTP_400_BAD_REQUEST)
        ser = CostCentersSaveSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            data = ser.data
            saveuserlog(request.user, f"Cost Center updated for account {data['ban']}")
            return Response({"message": "Cost Center updated successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "unable to update cost center."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request,org, pk, *args, **kwargs):
        obj = CostCenters.objects.filter(id=pk).first()
        ban = obj.ban
        cc = obj.cost_center
        if not obj:
            saveuserlog(request.user, f"Cost Center {cc} of account {ban} deleted.")
            return Response({"message": "Cost Center not found"}, status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response({"message": "Cost Center deleted successfully!"}, status=status.HTTP_200_OK)
    
class BulkCostCenterUpload(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request,sub_company,vendor,ban, *args, **kwargs):
        data = request.data.copy()
        data = data.get('costCenters')
        for center in data:
            dct = {}
            dct['sub_company'] = sub_company
            dct['vendor'] = vendor
            dct['ban'] = ban
            ba
            dct['cost_center'] = center
            ser = CostCentersSaveSerializer(data=dct)
            if ser.is_valid(): 
                ser.save()
            else:
                print(center)
                print(ser.errors)
        saveuserlog(request.user, f"Bulk Cost centers for {ban} uploaded successfully.")
        return Response({"message": "Cost Centers added successfully!"}, status=status.HTTP_200_OK)