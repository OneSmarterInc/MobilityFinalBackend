from Dashboard.ModelsByPage.cat import BaselineCategories
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.cat import catserializer, showcategoriesSerializer
from OnBoard.Ban.models import BaselineDataTable, BaseDataTable
from OnBoard.Ban.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors
from rest_framework.permissions import IsAuthenticated
from addon import parse_until_dict
from authenticate.views import saveuserlog
from Batch.views import create_notification
from django.forms.models import model_to_dict
from detect_model_changes import track_model_changes
class CategoryView(APIView):
    # permission_classes = [IsAuthenticated]
    
    def get(self, request,pk=None, *args, **kwargs):

        org = request.GET.get('sub_company')
        vendor = request.GET.get('vendor')
        ban = request.GET.get('ban')

        if pk:
            obj = BaselineCategories.objects.filter(organization=org, vendor=vendor, ban=ban, id=pk).first()
            if not obj:
                return Response({"message": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
            ser = showcategoriesSerializer(obj)
        else:
            objs = BaselineCategories.objects.filter(organization=org, vendor=vendor, ban=ban)
            ser = showcategoriesSerializer(objs,many=True)
        return Response({"data":ser.data}, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        org = request.data.get('organization')
        ven = request.data.get('vendor')
        ban = request.data.get('ban')
        cat = request.data.get('category')

        banObj = BaseDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(accountnumber=ban).first()
        if not banObj:
            return Response(
                {"message": "account number not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        data["banObj"] = banObj.id

        check =  BaselineCategories.objects.filter(organization=org, vendor=ven, ban=ban, category=cat)
        
        if check.exists():
            return Response(
                {"message": "Baseline category already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            ser = catserializer(data=data)
            if ser.is_valid():
                ser.save()
                saveuserlog(request.user, f"Baseline category {ser.data['category']} created for ban {ban}.")
                # create_notification(request.user, f"Baseline category {ser.data['category']} created for ban {ban}.",company=request.user.company)
                return Response({"message" : "new Category created successfully!"}, status=status.HTTP_201_CREATED)
            else:
                print(ser.errors)
                return Response({"message":"unable to create new category."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"message":"unable to create new category."}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request,pk, *args, **kwargs):
        try:
            obj = BaselineCategories.objects.filter(id=pk).first()
        except BaselineCategories.DoesNotExist():
            return Response({"message": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        data = request.data
        org = data.get('organization')
        ven = request.data.get('vendor')
        ban = request.data.get('ban')
        if not (org and ven and ban):
            return Response(
                {"message": "Missing required fields: organization, vendor, or BAN."},
                status=status.HTTP_400_BAD_REQUEST
            )
        data["banObj"] = obj.banObj.id
        original_data = model_to_dict(obj)
        data = request.data
        ser = catserializer(obj, data=data)
        if ser.is_valid():
            ser.save()
            change_log = track_model_changes(obj, original_data)
            saveuserlog(request.user, f"Updated Baseline Category [{ser.data['category']} | BAN: {ban}]: {change_log}")
            # create_notification(request.user, f"Baseline category {ser.data['category']} updated for ban {ban}.",request.user.company)
            return Response({"message" : "Category updated successfully!"}, status=status.HTTP_200_OK)
        else:
            print(ser.errors)
            return Response({"message":"unable to update category."}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request,pk, *args, **kwargs):
        try:
            category = BaselineCategories.objects.get(id=pk)
            ban = category.ban
            category.delete()
            saveuserlog(request.user, f"Baseline category {category} of ban {ban} deleted.")
            return Response({"message": "category deleted successfully!"}, status=status.HTTP_200_OK)
        except BaselineCategories.DoesNotExist:
            return Response({"message": "category does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"message":"unable to delete category."}, status=status.HTTP_400_BAD_REQUEST)
        

import json
def store_baseline_categories(objs, base_instance):
        if base_instance.banUploaded:
            vendor = base_instance.banUploaded.Vendor
            organization = base_instance.banUploaded.organization 
        elif base_instance.banOnboarded:
            vendor = base_instance.banOnboarded.vendor
            organization = base_instance.banOnboarded.organization 
        ban = base_instance.accountnumber
        from collections import defaultdict
        def extract_categories(objs):
            grouped = defaultdict(list)

            for obj in objs:
                raw = parse_until_dict(obj.category_object)
                if not isinstance(raw, dict):
                    continue

                for category, sub_dict in raw.items():
                    if not category or category == "NAN":
                        continue
                    if isinstance(sub_dict, dict):
                        sub_keys = list(sub_dict.keys())
                    else:
                        continue

                    grouped[category].extend(sub_keys)

            for k in grouped:
                grouped[k] = list(dict.fromkeys(grouped[k]))

            return grouped
        if not objs:
            return
        if not (organization and vendor and base_instance):
            return
        # 🔥 Step A — group everything
        grouped = extract_categories(objs)
        if not grouped:
            return

        # 🔥 Step B — fetch existing
        existing_qs = BaselineCategories.objects.filter(
            organization=organization,
            vendor=vendor,
            banObj=base_instance,
            ban=ban,
            category__in=grouped.keys()
        )

        existing_map = {obj.category: obj for obj in existing_qs}

        to_create = []
        to_update = []

        # 🔥 Step C — merge logic
        for category, new_list in grouped.items():
            if category in existing_map:
                obj = existing_map[category]

                existing = obj.sub_categories or []
                merged = list(dict.fromkeys(existing + new_list))

                if merged != existing:
                    obj.sub_categories = merged
                    to_update.append(obj)

            else:
                to_create.append(
                    BaselineCategories(
                        organization=organization,
                        vendor=vendor,
                        ban=ban,
                        banObj=base_instance,
                        category=category,
                        sub_categories=new_list
                    )
                )

        # 🔥 Step D — bulk write
        if to_create:
            BaselineCategories.objects.bulk_create(to_create)

        if to_update:
            BaselineCategories.objects.bulk_update(
                to_update,
                ["sub_categories"]
            )