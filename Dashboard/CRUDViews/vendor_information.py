from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.requestser import VendorInformationSerializer, showOrganizations,showVendorInformationSerializer,showplanevendorInformation, showOnboardedSerializer
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from ..ModelsByPage.Req import VendorInformation, VendorPlan
from OnBoard.Organization.models import Organizations
from OnBoard.Ban.models import BaseDataTable, BaselineDataTable, UniquePdfDataTable
from authenticate.views import saveuserlog
class getBansView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request,org, *args, **kwargs):
        if not org:
            return Response({"message":"sub company not found!"},status=status.HTTP_400_BAD_REQUEST)
        objs = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(sub_company=org)
        ser = showOnboardedSerializer(objs, many=True)

        return Response({"data":ser.data},status=status.HTTP_200_OK)
    
import json
class VendorInformationView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = VendorInformation.objects.filter(sub_company=pk)
            ser = showVendorInformationSerializer(obj, many=True)
            return Response({"data":ser.data},status=status.HTTP_200_OK)
        else:
            orgs = Organizations.objects.exclude(status=False)
            org_ser = showOrganizations(orgs,many=True)
            return Response({"orgs":org_ser.data},status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        vendor_plan = data.get('vendor_plan')
        if not vendor_plan:
            data['existing_plan'] = data.get('plan')
        else:
            data['existing_plan'] = None
        existing_plan = data.get('existing_plan')
        if VendorInformation.objects.filter(code=data.get('code')):
            return Response({"message":"This code already exists!"},status=status.HTTP_400_BAD_REQUEST)
        check_info = VendorInformation.objects.filter(sub_company=data.get('sub_company'),vendor=data.get("vendor"), ban=data.get("ban"))
        if not existing_plan and check_info.filter(vendor_plan=data.get('vendor_plan')).exists():
            return Response({"message":"Vendor information already exists!"},status=status.HTTP_400_BAD_REQUEST)
        if not vendor_plan and check_info.filter(existing_plan=data.get('existing_plan')).exists():
            return Response({"message":"Vendor information already exists!"},status=status.HTTP_400_BAD_REQUEST)
        ser = VendorInformationSerializer(data=data)
        if ser.is_valid():
            ser.save()

            show_data = showplanevendorInformation(VendorInformation.objects.filter(id=ser.data['id']).first()).data
            new_category = self.format_category(show_data['baseline_object'])
            if vendor_plan and data.get('plan_to_replace'):
                print("replacing")
                vendor_plan_obj = VendorPlan.objects.filter(id=vendor_plan).first()
                updated_plan = {
                    "plans" : vendor_plan_obj.plan,
                    "plan_type": vendor_plan_obj.plan_type,
                    "data_allotment" : vendor_plan_obj.data_allotment,
                    "plan_fee": vendor_plan_obj.plan_fee,
                    "smartphone" :vendor_plan_obj.smartphone,
                    "tablet_computer" :vendor_plan_obj.tablet_computer,
                    "mifi" : vendor_plan_obj.mifi,
                    "wearables" : vendor_plan_obj.wearables
                }
                replace_plan = data.get('plan_to_replace')
                baseline = self.get_query(BaselineDataTable, show_data).filter(plans=replace_plan)
                baseline.update(category_object=new_category, **updated_plan)
                unique = self.get_query(UniquePdfDataTable, show_data).filter(plans=replace_plan)
                unique.update(category_object=new_category, **updated_plan)
                VendorInformation.objects.filter(id=show_data['id']).update(plan_replaced_with=replace_plan)
                
            if existing_plan and data.get('update_existing'):
                print("replacing")
                baseline = self.get_query(BaselineDataTable, show_data).filter(plans=existing_plan)
                baseline.update(category_object=new_category)
                unique = self.get_query(UniquePdfDataTable, show_data).filter(plans=existing_plan)
                unique.update(category_object=new_category)
                VendorInformation.objects.filter(id=show_data['id']).update(plan_replaced_with=existing_plan)
            saveuserlog(request.user, f"vendor information added in account number {data.get('ban')}")
            return Response({"message":"vendor information added succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":str(ser.errors)},status=status.HTTP_400_BAD_REQUEST)
    def get_query(self, model,data):
        query = model.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=data.get('sub_company'),vendor=data.get("vendor"), account_number=data.get("ban"))
        return query
    def format_category(self, cat):
        result = {}
        for item in cat:
            cat = item["category"]
            sub_cat = item["sub_category"]
            amount = item["amount"]
            result.setdefault(cat, {})[sub_cat] = amount

        return json.dumps(result)        

    def put(self, request, pk, *args, **kwargs):
        obj = VendorInformation.objects.filter(id=pk).first()
        if not obj:
            return Response({"message":"vendor information not found"},status=status.HTTP_400_BAD_REQUEST)
        print(request.data)
        ser = VendorInformationSerializer(obj,data=request.data,partial=True)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f"vendor information updated for account number {obj.ban}")
            return Response({"message":"vendor information updated succesfully!"},status=status.HTTP_200_OK)
        else:
            return Response({"message":"Unable to update vendor information."},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk, *args, **kwargs):
        obj = VendorInformation.objects.filter(id=pk).first()
        ban = obj.ban
        if not obj:
            return Response({"message":"vendor information not found"},status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        saveuserlog(request.user, f"vendor information updated for account number {ban}")
        return Response({"message":"vendor information deleted sucessfully!"},status=status.HTTP_200_OK)
    

class ReplacePlanView(APIView):
    permission_classes = [IsAuthenticated]
    def get_query(self, model,data):
        query = model.objects.exclude(banOnboarded=None, banUploaded=None).filter(sub_company=data.get('sub_company'),vendor=data.get("vendor"), account_number=data.get("ban"))
        return query
    def format_category(self, cat):
        result = {}
        for item in cat:
            cat = item["category"]
            sub_cat = item["sub_category"]
            amount = item["amount"]
            result.setdefault(cat, {})[sub_cat] = amount

        return json.dumps(result)
    def put(self,request,pk,*args,**kwargs):
        obj = VendorInformation.objects.filter(id=pk).first()
        show_data = showplanevendorInformation(obj).data
        if not obj:
            return Response({"message":"vendor information not found"},status=status.HTTP_400_BAD_REQUEST)
        print(request.data)
        data = request.data.copy()
        vendor_plan_obj = VendorPlan.objects.filter(id=obj.vendor_plan.id).first()
        print(vendor_plan_obj)
        updated_plan = {
            "plans" : vendor_plan_obj.plan,
            "plan_type": vendor_plan_obj.plan_type,
            "data_allotment" : vendor_plan_obj.data_allotment,
            "plan_fee": vendor_plan_obj.plan_fee,
            "smartphone" :vendor_plan_obj.smartphone,
            "tablet_computer" :vendor_plan_obj.tablet_computer,
            "mifi" : vendor_plan_obj.mifi,
            "wearables" : vendor_plan_obj.wearables
        }
        replace_plan = data.get('selected_plan')
        new_cat = self.format_category(obj.baseline_object)
        baseline = self.get_query(BaselineDataTable, show_data).filter(plans=replace_plan)
        baseline.update(category_object=new_cat, **updated_plan)
        unique = self.get_query(UniquePdfDataTable, show_data).filter(plans=replace_plan)
        unique.update(category_object=new_cat, **updated_plan)
        VendorInformation.objects.filter(id=show_data['id']).update(plan_replaced_with=replace_plan)
        saveuserlog(request.user, f"vendor information updated for account number {obj.ban}")
        return Response({"message":"plan replaced succesfully!"},status=status.HTTP_200_OK)