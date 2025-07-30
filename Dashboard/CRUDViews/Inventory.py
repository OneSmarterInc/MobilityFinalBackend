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
from addon import parse_until_dict
import json

class InventoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,org,pk=None, *args, **kwargs):
        if pk:
            inventory = UniquePdfDataTable.objects.filter(sub_company=org).filter(viewuploaded=None,viewpapered=None).filter(id=pk).order_by('-account_number').order_by('-created')
        else:
            inventory = UniquePdfDataTable.objects.filter(sub_company=org).filter(viewuploaded=None,viewpapered=None).order_by('-account_number').order_by('-created')
        if request.user.designation.name == "Superadmin":
            all_accnts = showBaseDataser(BaseDataTable.objects.filter(sub_company=org).filter(viewuploaded=None,viewpapered=None), many=True)
        else:
            all_accnts = showBaseDataser(BaseDataTable.objects.filter(sub_company=org).filter(viewuploaded=None,viewpapered=None).filter(company=request.user.company.Company_name), many=True)

        serializer = UniqueTableShowSerializer(inventory, many=True)
        return Response({"data":serializer.data, "accounts":all_accnts.data}, status=status.HTTP_200_OK)
    
    def post(self, request,org, *args, **kwargs):
        return Response({"message": "Post"}, status=status.HTTP_200_OK)
    def data_filter(self, data):
        return {
            k: v for k, v in data.items()
            if str(v).lower() not in ('nan', 'null','na') and v is not None
        }
    def put(self, request,org,pk=None, *args, **kwargs):
        data = request.data
        
        if not pk:
            try:
                for inv in data:
                    print(inv)
                    obj = UniquePdfDataTable.objects.filter(sub_company=org).get(id=inv.get('id'))
                    print(obj)
                    
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
                    wn = inv.get('Wireless_number')
                    inv['Wireless_number'] = wn
                    baseline_obj = BaselineDataTable.objects.filter(sub_company=org).filter(account_number=obj.account_number, Wireless_number=obj.wireless_number, vendor=obj.vendor)
                    if baseline_obj:
                        baselineser = BaselineTableSaveSerializer(baseline_obj[0], data=inv, partial=True)
                        if baselineser.is_valid():
                            baselineser.save()
                        else:
                            print(ser.errors)
                            return Response({"message":f"Unexpected error {ser.errors}"}, status=status.HTTP_400_BAD_REQUEST)
                return Response({"message":"Inventories updated successfully"}, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({"message":f"Unexpected error {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            

        
        new_data = self.data_filter(data)
        data = new_data
        co = data.get("category_object")
        co = parse_until_dict(co) if co else None
        data["category_object"] = json.dumps(co) if co else {}
        try:
            unique_obj = UniquePdfDataTable.objects.filter(sub_company=org).filter(id=pk)
            baseline_obj = BaselineDataTable.objects.filter(sub_company=org).filter(account_number=unique_obj[0].account_number, Wireless_number=unique_obj[0].wireless_number)
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
            wn = data.get('wireless_number')
            data['Wireless_number'] = wn
            if baseline_obj:
                baseline_ser = BaselineTableShowSerializer(baseline_obj[0], data, partial=True)
                if baseline_ser.is_valid():
                    baseline_ser.save()
                else:
                    print(baseline_ser.errors)
                    return Response({"message": str(baseline_ser.errors)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"message": "inventory updated successfully!"}, status=status.HTTP_200_OK)
            
        else:
                return Response({"message": str(unique_ser.errors)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request,org, pk, *args, **kwargs):
        try:
            inventoryunique = UniquePdfDataTable.objects.filter(sub_company=org).get(id=pk)
            inventorybaseline = BaselineDataTable.objects.filter(sub_company=org).filter(banUploaded=inventoryunique.banUploaded, banOnboarded=inventoryunique.banOnboarded).get(Wireless_number=inventoryunique.wireless_number)
            inventoryunique.delete()
            inventorybaseline.delete()
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
    
        all_accnts = showBaseDataser(BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).filter(sub_company=org), many=True)
        
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
    
from django.forms.models import model_to_dict
import pandas as pd
import os
from django.conf import settings

class DownloadInventoryExcel(APIView):
    def post(self, request, org, *args, **kwargs):
        inventory_data = UniquePdfDataTable.objects.filter(sub_company=org).filter(viewuploaded=None,viewpapered=None)
        data = request.data
        is_all = data.get('download_all')
        vendor = data.get('vendor_name')
        User_status = data.get('User_status')
        upgrade_eligibility_date = data.get('upgrade_eligibility_date')
        device_type = data.get('Devices_device_type')
        Location_code = data.get('Location_code')

        if not is_all:
            inventory_data = inventory_data.filter(vendor=vendor) if not 'All' in vendor else inventory_data
            inventory_data = inventory_data.filter(User_status=User_status) if not 'All' in User_status else inventory_data
            inventory_data = inventory_data.filter(upgrade_eligible_date=upgrade_eligibility_date) if not 'All' in upgrade_eligibility_date else inventory_data
            inventory_data = inventory_data.filter(Devices_device_type=device_type) if not 'All' in device_type else inventory_data
            inventory_data = inventory_data.filter(Location_zip=Location_code) if not 'All' in Location_code else inventory_data


        if not inventory_data:
            return Response({"message":"No data found with given filters"},status=status.HTTP_400_BAD_REQUEST)

        inventory_data = [model_to_dict(obj) for obj in inventory_data]
        inventory_data = pd.DataFrame(inventory_data)
        inventory_data = inventory_data.drop(columns=['id', 'banOnboarded', 'banUploaded', 'inventory', 'viewuploaded',
       'viewpapered','category_object', 'is_baseline_approved'])
        inventory_dir = os.path.join(settings.MEDIA_ROOT, 'inventory')
        os.makedirs(inventory_dir, exist_ok=True)

        # File path
        file_name = 'inventory.xlsx'
        file_path = os.path.join(inventory_dir, file_name)

        # Save the DataFrame to Excel
        inventory_data.to_excel(file_path, index=False)

        # Return relative media URL
        return Response({
            "message": "Excel downloaded successfully!",
            "file_path": f"{settings.MEDIA_URL}inventory/{file_name}"
        }, status=status.HTTP_200_OK)
