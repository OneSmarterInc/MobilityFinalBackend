from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.auth import login, logout
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from OnBoard.Company.models import Company
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from authenticate.models import PortalUser
from OnBoard.Ban.models import UniquePdfDataTable
from Dashboard.Serializers.requestser import EmployeeSerializer, SaveUpgradeDeviceRequestSerializer
from authenticate.views import saveuserlog

class EmployeeRequest(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, email, *args, **kwargs):
        get_user = PortalUser.objects.filter(email=email).first()
        print(get_user)
        if not get_user:
            return Response({"message":f"Employee with email {email} not found."},status=status.HTTP_400_BAD_REQUEST)
        
        get_user_records = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(wireless_number=get_user.mobile_number).first()
        if not get_user_records:
            return Response({"message":f"Records of user {get_user.email} not found!"},status=status.HTTP_400_BAD_REQUEST)
        ser = EmployeeSerializer(get_user_records)
        print(ser.data)
        return Response({"data":ser.data},status=status.HTTP_200_OK)

    
from ..ModelsByPage.Req import upgrade_device_request
class DeviceUpgradeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, email, *args, **kwargs):
        data = request.data
        get_user = PortalUser.objects.filter(email=email).first()
        print(data)
        if not get_user:
            return Response({"message":f"Employee with email {email} not found."},status=status.HTTP_400_BAD_REQUEST)
        
        get_user_records = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(wireless_number=get_user.mobile_number).first()
        if not get_user_records:
            return Response({"message":f"Records of user {get_user.email} not found!"},status=status.HTTP_400_BAD_REQUEST)
        
        ser = SaveUpgradeDeviceRequestSerializer(data=data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, "upgrade device request raised by user")
            return Response({"message": "Your request to upgrade the device is submitted successfully."},status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message": "Unable to submit device upgrade request."},status=status.HTTP_400_BAD_REQUEST)
