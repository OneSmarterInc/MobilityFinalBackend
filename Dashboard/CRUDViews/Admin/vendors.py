
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import Vendors
from ...Serializers.AdminPage import VendorsOperationSerializer, VendorsShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog

class VendorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            vendor = Vendors.objects.get(name=pk)
            ser = VendorsShowSerializer(vendor)
            return Response({"data":ser.data}, status=status.HTTP_200_OK)
        else:
            vendors = Vendors.objects.all()
            ser = VendorsShowSerializer(vendors, many=True)
            return Response({"data":ser.data}, status=status.HTTP_200_OK)
    
    def post(self, request):
        ser = VendorsOperationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f'new vendor created {ser.data["name"]}')  # save log here  # todo: add logging functionality
            return Response({"message" : "new vendor created successfully!", "data" : ser.data}, status=status.HTTP_201_CREATED)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)

    
    def put(self, request, pk):
        try:
            vendor = Vendors.objects.get(name=pk)
        except Vendors.DoesNotExist:
            return Response({"message": 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)
        ser = VendorsOperationSerializer(vendor, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'vendor updated: {ser.data["name"]}')  # save log here  # todo: add logging functionality  # todo: add logging functionality
            return Response({"message" : "vendor updated successfully!", "data":ser.data}, status=status.HTTP_200_OK)
        return Response({"message": ser.errors}, status=status.HTTP_400_BAD_REQUEST)


    
    def delete(self, request, pk):
        try:
            vendor = Vendors.objects.get(name=pk)
            vendor.delete()
            saveuserlog(request.user, description=f'vendor deleted: {pk}')  # sav
            return Response({'message': "Vendor Deleted Successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)