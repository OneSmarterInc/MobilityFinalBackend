from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from OnBoard.Company.models import Company
from rest_framework.permissions import IsAuthenticated
from OnBoard.Ban.models import UniquePdfDataTable, BaselineDataTable, BaseDataTable, UploadBAN
from ..Serializers.inventory import UniqueTableShowSerializer, OrganizationsShowSerializer, BaselineTableShowSerializer, showBaseDataser, VendorsSerializer, UniqueTableSaveSerializer, BaselineTableSaveSerializer
import ast
from OnBoard.Organization.models import Organizations

class InventoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        if pk:
            inventory = UniquePdfDataTable.objects.filter(viewuploaded=None).filter(id=pk).order_by('-account_number').order_by('-created')
        else:
            inventory = UniquePdfDataTable.objects.filter(viewuploaded=None).order_by('-account_number').order_by('-created')
        if request.user.designation.name == "Superadmin":
            orgs = Organizations.objects.all()
        else:
            orgs = Organizations.objects.filter(company=request.user.company)

        all_accnts = showBaseDataser(BaseDataTable.objects.filter(viewuploaded=None).filter(company=request.user.company.Company_name), many=True)
        
        serializer = UniqueTableShowSerializer(inventory, many=True)
        orgser = OrganizationsShowSerializer(orgs, many=True)
        return Response({"orgs":orgser.data, "data":serializer.data, "accounts":all_accnts.data}, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        return Response({"message": "Post"}, status=status.HTTP_200_OK)
    def data_filter(self, data):
        return {
            k: v for k, v in data.items()
            if str(v).lower() not in ('nan', 'null','na') and v is not None
        }
    def put(self, request,pk=None, *args, **kwargs):
        data = request.data
        if not pk:
            try:
                for inv in data:
                    
                    obj = UniquePdfDataTable.objects.get(id=inv.get('id'))
                    if (obj.banOnboarded):
                        inv['banOnboarded'] = obj.banOnboarded.id
                    if (obj.banUploaded):
                        inv['banUploaded'] = obj.banOnboarded.id
                    
                    ser = UniqueTableSaveSerializer(obj, data=inv, partial=True)
                    if ser.is_valid():
                        ser.save()
                    else:
                        print(ser.errors)
                        return Response({"message":f"Unexpected error {ser.errors}"}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"message":"Inventories updated successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({"message":f"Unexpected error {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            

        print(pk)
        
        new_data = self.data_filter(data)
        data = new_data
        try:
            unique_obj = UniquePdfDataTable.objects.filter(id=pk)
            print("********", unique_obj[0].wireless_number, unique_obj[0].account_number)
            baseline_obj = BaselineDataTable.objects.filter(account_number=unique_obj[0].account_number, Wireless_number=unique_obj[0].wireless_number)
            print(unique_obj, baseline_obj)
        except UniquePdfDataTable.DoesNotExist:
            return Response({"message": "Inventory not found in unique table!"}, status=status.HTTP_404_NOT_FOUND)
        except BaselineDataTable.DoesNotExist:
            return Response({"message": "Inventory not found in baseline table!"}, status=status.HTTP_404_NOT_FOUND)
        if 'action' in data:
            if data['action'] == 'move-ban':
                ban = data['ban']
                obj1 = unique_obj[0]
                prev = obj1.account_number
                obj1.account_number = ban
                obj1.save()
                if baseline_obj:
                    obj1 = baseline_obj[0]
                    obj1.account_number = ban
                    obj1.save()
                return Response({"message":f"Ban successfully moved from {prev} to {ban}"},status=status.HTTP_200_OK)
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


class AddNewInventoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,org, *args, **kwargs):
        
        try:
            organization = Organizations.objects.filter(Organization_name=org)
        except Organizations.DoesNotExist:
            return Response({"message":f"Organization {org} not found!"})
        vendors = VendorsSerializer(organization[0].vendors.all(), many=True)
        print(vendors.data)
    
        all_accnts = showBaseDataser(BaseDataTable.objects.filter(viewuploaded=None).filter(sub_company=org), many=True)
        print(all_accnts.data)
        
        return Response({"accounts":all_accnts.data, "vendors":vendors.data}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        base = BaseDataTable.objects.filter(accountnumber=data.get('account_number'), vendor=data.get('vendor'), company=data.get('company'), sub_company=data.get('sub_company'))
        if base[0].banOnboarded:
            data['banOnboarded'] = base[0].banOnboarded.id
        elif base[0].banUploaded:
            data['banUploaded'] = base[0].banUploaded.id

        if not base:
            return Response({"message":"Account number not found!"},status=status.HTTP_400_BAD_REQUEST)
        check_presence = UniquePdfDataTable.objects.filter(account_number=data.get('account_number'), vendor=data.get('vendor'), company=data.get('company'), sub_company=data.get('sub_company'), wireless_number=data.get('wireless_number'))
        if check_presence:
            return Response({"message":f"Wirelss number {data.get('wireless_number')} with account number {data.get('account_number')} already present!"},status=status.HTTP_400_BAD_REQUEST)
        uniqueser = UniqueTableSaveSerializer(data=data)
        if uniqueser.is_valid():
            uniqueser.save()
        else:
            print(uniqueser.errors)
            return Response({"message":str(uniqueser.errors)},status=status.HTTP_400_BAD_REQUEST)
        wn = data.get('wireless_number')
        data['Wireless_number'] = wn
        baselineser = BaselineTableSaveSerializer(data=data)
        if baselineser.is_valid():
            baselineser.save()
            return Response({"message":"New inventory created successfully!"}, status=status.HTTP_200_OK)
        else:
            print(baselineser.errors)
            return Response({"message":str(baselineser.errors)},status=status.HTTP_400_BAD_REQUEST)
        