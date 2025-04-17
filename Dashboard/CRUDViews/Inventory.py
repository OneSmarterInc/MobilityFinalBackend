from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Company.models import Company
from rest_framework.permissions import IsAuthenticated
from OnBoard.Ban.models import UniquePdfDataTable, BaselineDataTable
from ..Serializers.inventory import UniqueTableShowSerializer, OrganizationsShowSerializer, BaselineTableShowSerializer
from OnBoard.Organization.models import Organizations

class InventoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        if pk:
            inventory = UniquePdfDataTable.objects.filter(id=pk)
        else:
            inventory = UniquePdfDataTable.objects.all()
        if request.user.designation.name == "Superadmin":
            orgs = Organizations.objects.all()
        else:
            orgs = Organizations.objects.filter(company=request.user.company)
        
        serializer = UniqueTableShowSerializer(inventory, many=True)
        orgser = OrganizationsShowSerializer(orgs, many=True)
        return Response({"orgs":orgser.data, "data":serializer.data}, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        return Response({"message": "Post"}, status=status.HTTP_200_OK)
    def data_filter(self, data):
        return {
            k: v for k, v in data.items()
            if str(v).lower() not in ('nan', 'null','na') and v is not None
        }
    def put(self, request,pk, *args, **kwargs):
        data = request.data
        print("data=", data)
        new_data = self.data_filter(data)
        data = new_data
        print("new data=", data)
        try:
            unique_obj = UniquePdfDataTable.objects.filter(id=pk)
            print(unique_obj[0].wireless_number)
            baseline_obj = BaselineDataTable.objects.filter(account_number=unique_obj[0].account_number, Wireless_number=unique_obj[0].wireless_number)
            print(unique_obj, baseline_obj)
        except UniquePdfDataTable.DoesNotExist:
            return Response({"message": "Inventory not found in unique table!"}, status=status.HTTP_404_NOT_FOUND)
        except BaselineDataTable.DoesNotExist:
            return Response({"message": "Inventory not found in baseline table!"}, status=status.HTTP_404_NOT_FOUND)
        unique_ser = UniqueTableShowSerializer(unique_obj[0], data, partial=True)
        if unique_ser.is_valid():
            unique_ser.save()
            print(unique_ser.data)
            baseline_ser = BaselineTableShowSerializer(baseline_obj[0], data, partial=True)
            if baseline_ser.is_valid():
                baseline_ser.save()
                return Response({"message": "inventory updated successfully!"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": str(baseline_ser.errors)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
                return Response({"message": str(unique_ser.errors)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request, pk, *args, **kwargs):
        try:
            inventory = UniquePdfDataTable.objects.get(id=pk)
            inventory.delete()
            return Response({"message": "Inventory deleted successfully"}, status=status.HTTP_200_OK)
        except UniquePdfDataTable.DoesNotExist:
            return Response({"message": "Inventory not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Delete"}, status=status.HTTP_200_OK)