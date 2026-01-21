from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from OnBoard.Company.models import Company
from OnBoard.Organization.models import Organizations
from OnBoard.Location.models import Location
from Dashboard.ModelsByPage.DashAdmin import Vendors
from .ser import OrganizationgetNameSerializer, CompanygetNameSerializer, LocationGetNameSerializer, VendorNameSerializer
from .ser import OrganizationGetAllDataSerializer, CompanygetAllDataSerializer, LocationGetAllDataSerializer, VendorGetAllDataSerializer
from .ser import CompanyShowOnboardSerializer, OrganizationShowOnboardSerializer, BanShowSerializer, OnboardBanshowserializer, BaseDataTableShowSerializer, UploadBANSerializer, UniqueTableShowSerializer, BaselineSaveSerializer, showallSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog
from detect_model_changes import track_model_changes
from OnBoard.Ban.models import UploadBAN, OnboardBan, BaseDataTable, BaselineDataTable
# Create your views here.
from .homeser import showCompanySerializer, showOnboardedSerializer, showOrganizationSerializer, showUploadedSerializer
class GetCompanyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        companies = Company.objects.all()
        comser = showCompanySerializer(companies, many=True)
        return Response({"companies":comser.data},status=status.HTTP_200_OK)
from django.db.models import Q

class Homepageview(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request,company):
        try:
            org = request.user.organization
            obj = Company.objects.filter(Company_name=company).first()
            if not obj:
                return Response({"message":"Company not found!"},status=status.HTTP_400_BAD_REQUEST)
            orgs = Organizations.objects.filter(company=request.user.company) if not org else Organizations.objects.filter(id=org.id)
            orgser = showOrganizationSerializer(orgs, many=True)
            bansOnboardSer = showOnboardedSerializer(OnboardBan.objects.filter(organization__in=orgs), many=True)
            bansUplaodSer = showUploadedSerializer(UploadBAN.objects.filter(organization__in=orgs), many=True)
            return Response({"onboarded":bansOnboardSer.data, "uploaded":bansUplaodSer.data, "orgs":orgser.data},status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message":"Interal Server Error!"},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class InventorySubjectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        if not org:
            objs = Company.objects.all()
            onboardbanObjs = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None)
            onbanser = BaseDataTableShowSerializer(onboardbanObjs, many=True)
            serializer = CompanyShowOnboardSerializer(objs, many=True)
            all_lines = UniquePdfDataTable.objects.exclude(banOnboarded=None, banUploaded=None)
            lines_Ser = UniqueTableShowSerializer(all_lines, many=True)
            return Response({"data": serializer.data, 'banonboarded':onbanser.data, "lines":lines_Ser.data}, status=status.HTTP_200_OK)
        else:
            objs = Organizations.objects.filter(id=org.id)
            serializer = OrganizationShowOnboardSerializer(objs, many=True)
            onboardbanObjs = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(Q(banUploaded__organization=org) | Q(banOnboarded__organization=org))
            onbanser = BaseDataTableShowSerializer(onboardbanObjs, many=True)
            all_lines = UniquePdfDataTable.objects.exclude(banOnboarded=None, banUploaded=None)
            lines_Ser = UniqueTableShowSerializer(all_lines, many=True)
            return Response({"data": serializer.data, 'banonboarded':onbanser.data, "lines":lines_Ser.data}, status=status.HTTP_200_OK)

from django.db.models import Q
class InventoryDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subject=None):
        try:
            if subject == "Company":
                company = Company.objects.all()
                serializer = CompanygetAllDataSerializer(company, many=True)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            elif subject == "Organization":
                organization = Organizations.objects.all()
                serializer = OrganizationGetAllDataSerializer(organization, many=True)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            elif subject == "Location":
                location = Location.objects.all()
                serializer = LocationGetAllDataSerializer(location, many=True)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            elif subject == "Vendor":
                vendor = Vendors.objects.all()
                serializer = VendorGetAllDataSerializer(vendor, many=True)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"message" : "Invalid subject"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"message": "Error getting data"}, status=status.HTTP_401_UNAUTHORIZED)
    
    def delete(self, request, subject, id):
        try:
            if subject == "Company":

                company = Company.objects.filter(id=id).first()
                name = company.Company_name
                company.delete()
                saveuserlog(request.user, f"Company named {name} deleted successfully!")
                # create_notification(request.user, f"Company named {name} deleted successfully!",request.user.company)
                return Response({"message": "company deleted successfully!"}, status=status.HTTP_200_OK)
            elif subject == "Organization":
                organization = Organizations.objects.filter(id=id).first()
                name = organization.Organization_name
                organization.delete()
                saveuserlog(request.user, f"Organization named {name} deleted successfully!")
                create_notification(request.user, f"Organization named {name} deleted successfully!",request.user.company)
                return Response({"message" : "organization deleted successfully!"}, status=status.HTTP_200_OK)
            elif subject == "Location":
                location = Location.objects.filter(id=id).first()
                name = location.site_name
                location.delete()
                saveuserlog(request.user, f"Location named {name} deleted successfully!")
                # create_notification(request.user, f"Location named {name} deleted successfully!",request.user.company)
                return Response({"message" : "Location deleted successfully!"}, status=status.HTTP_200_OK)
            elif subject == "Vendor":
                vendor = Vendors.objects.filter(id=id)
                name = vendor.name
                vendor.delete()
                saveuserlog(request.user, f"Vendor named {name} deleted successfully!")
                # create_notification(request.user, f"Vendor named {name} deleted successfully!",request.user.company)
                return Response({"message" : "Vendor deleted successfully!"}, status=status.HTTP_200_OK)
            else:
                return Response({"message" : "Invalid subject"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"message": "Error getting data"}, status=status.HTTP_401_UNAUTHORIZED)


from OnBoard.Organization.ser import DivisionNameSerializer
from OnBoard.Organization.models import Division
from OnBoard.Ban.models import PortalInformation
from .ser import UniqueTableShowSerializer, BanSaveSerializer, BaseDataTableAllShowSerializer
from OnBoard.Ban.PortalInfo.ser import showPortalInfoser
from Batch.views import create_notification
class BanInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org, vendor, ban, *args, **kwargs):
        try:
            orgobject = Organizations.objects.get(Organization_name=org)
            locobj = Location.objects.filter(organization=orgobject)
            vendorobject = Vendors.objects.get(name=vendor)
            banobject = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).get(sub_company=org, vendor=vendor, accountnumber=ban)
            if banobject.banUploaded:
                portalinfo = PortalInformation.objects.get(banUploaded=banobject.banUploaded.id)
            elif banobject.banOnboarded:
                portalinfo = PortalInformation.objects.get(banOnboarded=banobject.banOnboarded.id)
            banser = BanShowSerializer(banobject)
            pser = showPortalInfoser(portalinfo)
        except Organizations.DoesNotExist:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        except Vendors.DoesNotExist:
            return Response({"message": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)
        except BaseDataTable.DoesNotExist:
            return Response({"message": "Ban not found"}, status=status.HTTP_404_NOT_FOUND)
                
        banlines = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None)
        vendorser = VendorGetAllDataSerializer(vendorobject)
        orgser = OrganizationGetAllDataSerializer(orgobject)
        locser = LocationGetAllDataSerializer(locobj, many=True)

        divisions = DivisionNameSerializer(Division.objects.filter(organization=orgobject), many=True)

        allonboards = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(sub_company=org)


        allonboards = BaseDataTableAllShowSerializer(allonboards, many=True)


        return Response({
            "organization": orgser.data,
            "vendor": vendorser.data,
            "ban": banser.data,
            "locations": locser.data,
            "onboarded": allonboards.data,
            "divisions" : divisions.data,
            "linesall" : UniqueTableShowSerializer(banlines,many=True).data,
            "portal":pser.data
            }, status=status.HTTP_200_OK)
    
    def post(self, request, org, vendor, ban, *args, **kwargs):
        try:
            obj = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(sub_company=org, vendor=vendor, accountnumber=ban)
        except:
            return Response(
                {"message": "Ban not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        obj = obj[0] 
        original_data = {f.name: getattr(obj, f.name) for f in obj._meta.fields}

        if request.data['type'] == 'add-remark':
            obj.remarks = request.data['remarks']
            obj.save()
        elif request.data['type'] == 'add-contract':
            obj.contract_file = request.data['file']
            obj.contract_name = request.data['filename']
            obj.save()
        else:
            return Response(
                {"message": "Invalid request type."},
                status=status.HTTP_400_BAD_REQUEST
            )
        print(obj.remarks)
        
        change_log = track_model_changes(obj, original_data)
        msg = f"Following fields are updated of account number {obj.accountnumber} : {change_log}"
        saveuserlog(request.user, description=msg)
        # create_notification(request.user, f"account number {obj.accountnumber} updated",request.user.company)
        return Response({
            "message": "Ban information updated successfully!"
        }, status=status.HTTP_200_OK)
    
    def put(self, request, org, vendor, ban, *args, **kwargs):
        
        obj_qs = BaseDataTable.objects.filter(sub_company=org, vendor=vendor, accountnumber=ban)

        if not obj_qs.exists():
            return Response({"message": f"BAN with account number {ban} not found!"}, status=status.HTTP_400_BAD_REQUEST)

        instance = obj_qs.first()
        original_data = {f.name: getattr(instance, f.name) for f in instance._meta.fields}

        data = request.data.copy()

        serializer = BanSaveSerializer(instance, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            
            change_log = track_model_changes(instance, original_data)
            msg = f"Following fields are updated of account number {instance.accountnumber} : {change_log}"
            saveuserlog(request.user, description=msg)


            return Response({"message": "Ban updated successfully"}, status=status.HTTP_200_OK)

        else:
            return Response({"message": "Unable to update ban.", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, org, vendor, ban, *args, **kwargs):
        
        base = BaseDataTable.objects.filter(sub_company=org, vendor=vendor, accountnumber=ban)
        
        if not base:
            return Response({"message":f"Ban {ban} not found!"},status=status.HTTP_400_BAD_REQUEST)
        if base.exclude(viewuploaded=None,viewpapered=None).exists():
            return Response({"message":f"Deletion blocked. Ban '{ban}' has associated bills and cannot be deleted."},status=status.HTTP_400_BAD_REQUEST)
        if base[0].banOnboarded:
            obj = OnboardBan.objects.get(id=base[0].banOnboarded.id)
        elif base[0].banUploaded:
            obj = UploadBAN.objects.get(id=base[0].banUploaded.id)
        else:
            return Response({"message":f"Ban with account number {ban} not found!"},status=status.HTTP_400_BAD_REQUEST)
        acc = obj.account_number
        obj.delete()
        saveuserlog(request.user, f"account number {acc} deleted successfully.")
        # create_notification(user=request.user, msg=f"BAN {acc} deleted successfully!",company=request.user.company)
        return Response({"message":f"Ban with account number {ban} deleted successfully!"},status=status.HTTP_200_OK)
        

from Dashboard.ModelsByPage.DashAdmin import EntryType, BillType, PaymentType, InvoiceMethod, BanType, BanStatus, CostCenterLevel, CostCenterType
from OnBoard.Ban.uploadSer.ser import OrganizationShowuploadSerializer, CompanyShowSerializer, VendorShowSerializer, BanTypeShowSerializer, BanStatusShowSerializer, InvoiceMethodShowSerializer, PaymentTypeShowSerializer, CostCenterLevelShowSerializer, CostCenterTypeShowSerializer
from OnBoard.Ban.ser import EntryTypeShowSerializer, BillTypeShowSerializer

class UploadConsolidated(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(request, *args, **kwargs):
        orgs = Organizations.objects.all()
        orgserializer = OrganizationShowuploadSerializer(orgs, many=True)
        etypes = EntryType.objects.all()
        etypeserializer = EntryTypeShowSerializer(etypes, many=True)
        bans = UploadBAN.objects.all()
        serializer = UploadBANSerializer(bans, many=True)
        companies = Company.objects.all()
        companiesserializer = CompanyShowSerializer(companies, many=True)
        vendors = Vendors.objects.all()
        vendorsserializer = VendorShowSerializer(vendors, many=True)
        btypes = BillType.objects.all()
        btypeserializer = BillTypeShowSerializer(btypes, many=True)
        banstatuses = BanStatus.objects.all()
        banstatusesserializer = BanStatusShowSerializer(banstatuses, many=True)
        bantypes = BanType.objects.all()
        bantypeesserializer = BanTypeShowSerializer(bantypes, many=True)
        invoicemethods = InvoiceMethod.objects.all()
        invoicemethodsserializer = InvoiceMethodShowSerializer(invoicemethods, many=True)
        paymenttypes = PaymentType.objects.all()
        paymenttypesserializer = PaymentTypeShowSerializer(paymenttypes, many=True)
        costcenterlevels = CostCenterLevel.objects.all()
        costcenterlevelsserializer = CostCenterLevelShowSerializer(costcenterlevels, many=True)
        costcentertypes = CostCenterType.objects.all()
        costcentertypesserializer = CostCenterTypeShowSerializer(costcentertypes, many=True)
        return Response({
            "data" : serializer.data, 
            "organizations" : orgserializer.data, 
            'entrytypes' : etypeserializer.data, 
            "companies" : companiesserializer.data, 
            "vendors" : vendorsserializer.data, 
            "billtypes" : btypeserializer.data, 
            "banstatuses" : banstatusesserializer.data, 
            "bantypes" : bantypeesserializer.data,
            'invoicemethods' : invoicemethodsserializer.data,
            'paymenttypes' : paymenttypesserializer.data,
            'costcenterlevels' : costcenterlevelsserializer.data,
            'costcentertypes' : costcentertypesserializer.data,
            }, status=status.HTTP_200_OK)
    def post(request, *args, **kwargs):
        pass


from OnBoard.Ban.models import UniquePdfDataTable, Lines
from .ser import LineShowSerializer, UniqueTableShowSerializer, UniqueTableSaveSerializer, BaselineSaveSerializer
class Mobiles(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self,request, account, *args, **kwargs):

        mobiles = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(account_number=account)
        mobiles = UniqueTableShowSerializer(mobiles, many=True)

        acc = UploadBAN.objects.filter(account_number=account)[0]
        lines = Lines.objects.filter(account_number=acc)
        lines = LineShowSerializer(lines, many=True)

        return Response({
            "mobiles": mobiles.data,
            "lines": lines.data
        }, status=status.HTTP_200_OK)
from addon import parse_until_dict
import json
class MobileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request,account_number, wireless_number=None, *args, **kwargs):
        com = request.GET.get('company')
        sub_com = request.GET.get('sub_company')
        lines = UniquePdfDataTable.objects.exclude(banOnboarded=None, banUploaded=None).filter(account_number=account_number, company=com, sub_company=sub_com)
        
        if not wireless_number:
            lines = lines
        else:
            lines = lines.filter(wireless_number=wireless_number)
        
        lines = UniqueTableShowSerializer(lines, many=True)
        return Response({
            "lines": lines.data
        }, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        account_number = data.get('account_number', None)
        wireless_number = data.get('wireless_number', None)
        com = data.get('company', None)
        sub_com = data.get('sub_company', None)
        vendor = data.get('vendor', None)
        mainobject = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(company=com, sub_company=sub_com, account_number=account_number,vendor=vendor)
        if mainobject.filter(wireless_number=wireless_number).exists():
            return Response({
                "message": f"Mobile data with line {wireless_number} already exists"
            },status=status.HTTP_400_BAD_REQUEST)
        try:
            if mainobject[0].banOnboarded:
                data['banOnboarded'] = mainobject[0].banOnboarded.id
            elif mainobject[0].banUploaded:
                data['banUploaded'] = mainobject[0].banUploaded.id
            serializer = UniqueTableSaveSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                data['Wireless_number'] = wireless_number
                data['User_name'] = data.pop('user_name')
                baseser = BaselineSaveSerializer(data=data)
                if baseser.is_valid():
                    baseser.save()
                saveuserlog(request.user, f"new line with wireless number {data['wireless_number']} in account {data['account_number']} created successfully!")
                # create_notification(request.user, f"new line with wireless number {data['wireless_number']} in account {data['account_number']} created successfully!",request.user.company)
                return Response({
                    "message": f"new line with wireless number {data['wireless_number']} created successfully!"
                },status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response({
                    "message": "Unable to create new mobile line."
                },status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
            "message": "Unable to create new mobile line."
        },status=status.HTTP_400_BAD_REQUEST)

    def put(self, request,account_number,wireless_number, *args, **kwargs):
        data = request.data.copy()
        print(data)
        co = data.get("category_object")
        co = parse_until_dict(co) if co else None
        data["category_object"] = json.dumps(co) if co else {}
        obj = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(account_number=account_number, wireless_number=wireless_number).first()
        if not obj:
            return Response({"message":"Wireless Number not found!"},status=status.HTTP_400_BAD_REQUEST)
        print(obj)
        original_data = {f.name: getattr(obj, f.name) for f in obj._meta.fields}

        try:
            serializer = UniqueTableShowSerializer(obj, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                change_log = track_model_changes(obj, original_data)
                msg = f"Following fields are updated of wireless number {obj.wireless_number} : {change_log}"
                saveuserlog(request.user, description=msg)
            baselineobj = BaselineDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(account_number=account_number, Wireless_number=wireless_number).first()

            

            if baselineobj:
                baseline_ser = BaselineSaveSerializer(baselineobj, data=data, partial=True)
                if baseline_ser.is_valid():
                    baseline_ser.save()
            return Response({
                "message": f"mobile {wireless_number} updated successfully!"
            },status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({
            "message": "Unable to update mobile line."
        },status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request,account_number,wireless_number, *args, **kwargs):
        try:
            obj = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(account_number=account_number, wireless_number=wireless_number)
            if obj:
                obj = obj[0]
            else:
                return Response({
                    "message": "Mobile data not found"
                },status=status.HTTP_404_NOT_FOUND)
            obj.delete()
            saveuserlog(
                request.user,
                f'wireless number {wireless_number} in account number {account_number} deleted successfully!'
            )
            # create_notification(
            #     request.user,
            #     f'wireless number {wireless_number} in account number {account_number} deleted successfully!', request.user.company
            # )
            return Response({
                "message": f"mobile data of number {wireless_number} deleted successfully!"
            },status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
            "message": "Unable to delete mobile line."
        },status=status.HTTP_400_BAD_REQUEST)


class OnboardedBaselineView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org, vendor, ban, *args, **kwargs):
        try:
            if not org or not vendor or not ban:
                return Response({"message": "Organization, Vendor, and Ban parameters are required."}, status=status.HTTP_400_BAD_REQUEST)
            objs = BaselineDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(sub_company=org, vendor=vendor, account_number=ban)
            if not objs:
                return Response({"message": "No baseline data found for the given parameters."}, status=status.HTTP_404_NOT_FOUND)
            serializer = BaselineSaveSerializer(objs, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "Unable to get baseline data."}, status=status.HTTP_400_BAD_REQUEST)
        
class SearchView(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def return_msg(self, field):
        return Response({"message":f"query results for ban {field} not found"},status=status.HTTP_400_BAD_REQUEST)

    def return_respose(self,orgser,field,fieldser):
        return Response({
            "organization": orgser.data,
            f"{field}": fieldser.data,
            }, status=status.HTTP_200_OK)

    def get(self, request, *args, **kwargs):
        get_query = request.GET

        org = get_query.get('sub_company')
        ban = get_query.get('ban')

        la = get_query.get('location_address')
        lc = get_query.get('location_city')
        lcn = get_query.get('location_contact_name')
        ld = get_query.get('location_division')
        lp = get_query.get('location_phone')
        ln = get_query.get('location_name')
        ls = get_query.get('location_state')
        lz = get_query.get('location_zip')

        wn = get_query.get('wireless_number')
        username = get_query.get('username') 

        orgobj = Organizations.objects.filter(Organization_name=org).first()
        if not orgobj:
            return self.return_msg(org)
        orgser = OrganizationGetAllDataSerializer(orgobj)

        banobjects = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(sub_company=org)
        locs = Location.objects.filter(organization=orgobj)
        lines = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(sub_company=org)
        

        if ban:
            banobjects = banobjects.filter(accountnumber=ban)
            banser = showallSerializer(banobjects, many=True)
            return self.return_respose(orgser=orgser,field="bans", fieldser=banser)
        if not banobjects:return self.return_msg(ban)

        if wn: 
            lines=lines.filter(wireless_number=wn)
            lineser = UniqueTableSaveSerializer(lines, many=True)
            return self.return_respose(orgser=orgser,field="lines", fieldser=lineser)
        if not lines: return self.return_msg(wn)
        if username: 
            lines=lines.filter(user_name=username)
            return self.return_respose(orgser=orgser,field="lines", fieldser=lineser)
        if not lines: 
            return self.return_msg(username)

        
        return Response({"message": "query not found!"},status=status.HTTP_400_BAD_REQUEST)

    

# views.py
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

                

from django.db.models import Q
from django.core.exceptions import FieldError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

class BanInfoNoVendorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # ---------- helpers ------------------------------------------------------

    def _ban_base_qs(self):
        # Only live, de-duped base rows
        return BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None)

    def _get_org(self, org_slug: str):
        try:
            return Organizations.objects.get(Organization_name=org_slug)
        except Organizations.DoesNotExist:
            return None

    def _build_search_queryset(self, org: str, search_by: str, criteria: str):
        """
        Returns a queryset of BaseDataTable filtered by org + search key.
        search_by: 'ban' | 'wireless' | 'location'
        """
        search = (search_by or "").strip().lower()
        base = self._ban_base_qs().filter(sub_company=org)

        # 1) BAN → BaseDataTable.accountnumber
        if search == "ban":
            return base.filter(accountnumber=criteria)

        # 2) wireless → UniquePdfDataTable.wireless_number → distinct account_number → BaseDataTable.accountnumber
        if search in ("wireless", "wireless-number", "msisdn", "mobile"):
            up_lines = UniquePdfDataTable.objects.filter(
                viewuploaded=None, viewpapered=None,
                sub_company=org,
                wireless_number=criteria
            ).values_list("account_number", flat=True).distinct()
            acc_list = [a for a in up_lines if a]  # drop blanks/nulls
            if not acc_list:
                return self._ban_base_qs().none()
            return base.filter(accountnumber__in=acc_list)

        # 3) location → resolve Location in this org, then match BaseDataTable.location == str(Location.id)
        if "location" in search:
            orgobj = self._get_org(org)
            if not orgobj:
                return self._ban_base_qs().none()

            loc_qs = Location.objects.filter(organization=orgobj)
            loc = None

            # exact id
            if criteria.isdigit():
                loc = loc_qs.filter(id=int(criteria)).first()

            # soft match by common fields if not numeric (you can trim these if you only want id)

            if not loc:
                loc = loc_qs.filter(
                    Q(site_name__iexact=criteria) |
                    Q(alias__iexact=criteria) |
                    Q(physical_city__iexact=criteria) |
                    Q(physical_address__iexact=criteria)
                ).first()

            if not loc:
                return self._ban_base_qs().none()

            return_query = base.filter(location=str(loc.site_name))
            # BaseDataTable.location is CharField that stores the Location.id (as string)
            return return_query

        # Unknown mode → empty
        return self._ban_base_qs().none()

    def _resolve_vendor_obj(self, vendor_name: str):
        if not vendor_name:
            return None, Response({"message": "Vendor not linked to BAN"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            return Vendors.objects.get(name=vendor_name), None
        except Vendors.DoesNotExist:
            return None, Response({"message": "Vendor not found"}, status=status.HTTP_404_NOT_FOUND)

    # ---------- HTTP methods -------------------------------------------------

    def get(self, request, org, search_by, criteria, *args, **kwargs):
        # Org must exist
        orgobj = self._get_org(org)
        if not orgobj:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        qs = self._build_search_queryset(org, search_by, criteria)
        count = qs.count()

        if count == 0:
            return Response({"message": "No matches found."}, status=status.HTTP_404_NOT_FOUND)

        if count > 1:
            # Let the UI decide which BAN; send a compact serializer over BaseDataTable
            return Response(
                {
                    "message": "Multiple matches.",
                    "count": count,
                    "results": BaseDataTableAllShowSerializer(qs, many=True).data
                },
                status=status.HTTP_200_OK
            )

        # Exactly one BAN → full payload
        banobject = qs.first()
        vendorobj, vend_err = self._resolve_vendor_obj(banobject.vendor)
        if vend_err:
            return vend_err

        # Portal info (prefer uploaded, then onboarded)
        portalinfo = None
        try:
            if banobject.banUploaded:
                portalinfo = PortalInformation.objects.get(banUploaded=banobject.banUploaded.id)
            elif banobject.banOnboarded:
                portalinfo = PortalInformation.objects.get(banOnboarded=banobject.banOnboarded.id)
        except PortalInformation.DoesNotExist:
            portalinfo = None

        # Scoped related data
        loc_list_qs = Location.objects.filter(organization=orgobj)
        divisions_qs = Division.objects.filter(organization=orgobj)
        allonboards_qs = self._ban_base_qs().filter(sub_company=org)

        # Lines for this BAN (note: account_number in lines table)
        banlines = UniquePdfDataTable.objects.filter(
            viewuploaded=None, viewpapered=None,
            sub_company=org,
            account_number=banobject.accountnumber
        )

        data = {
            "organization": OrganizationGetAllDataSerializer(orgobj).data,
            "vendor": VendorGetAllDataSerializer(vendorobj).data,
            "ban": BanShowSerializer(banobject).data,
            "locations": LocationGetAllDataSerializer(loc_list_qs, many=True).data,
            "onboarded": BaseDataTableAllShowSerializer(allonboards_qs, many=True).data,
            "divisions": DivisionNameSerializer(divisions_qs, many=True).data,
            "linesall": UniqueTableShowSerializer(banlines, many=True).data,
            "portal": (showPortalInfoser(portalinfo).data if portalinfo else None),
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, org, search_by, criteria, *args, **kwargs):
        qs = self._build_search_queryset(org, search_by, criteria)
        count = qs.count()

        if count == 0:
            return Response({"message": "No matches found."}, status=status.HTTP_404_NOT_FOUND)
        if count > 1:
            return Response(
                {
                    "message": "Multiple matches; cannot apply a single update.",
                    "count": count,
                    "results": BaseDataTableAllShowSerializer(qs, many=True).data[:20],
                },
                status=status.HTTP_409_CONFLICT
            )

        obj = qs.first()
        original_data = {f.name: getattr(obj, f.name) for f in obj._meta.fields}
        req_type = request.data.get('type')

        if req_type == 'add-remark':
            obj.remarks = request.data.get('remarks', '')
            obj.save(update_fields=["remarks"])

        elif req_type == 'add-contract':
            file = request.FILES.get('file')
            filename = request.data.get('filename')
            if not file:
                return Response({"message": "file is required"}, status=status.HTTP_400_BAD_REQUEST)
            obj.contract_file = file
            if filename:
                obj.contract_name = filename
                obj.save(update_fields=["contract_file", "contract_name"])
            else:
                obj.save(update_fields=["contract_file"])

        else:
            return Response({"message": "Invalid request type."}, status=status.HTTP_400_BAD_REQUEST)
        change_log = track_model_changes(obj, original_data)
        msg = f"Following fields are updated of account number {obj.accountnumber} : {change_log}"
        saveuserlog(request.user, description=msg)

        return Response({"message": "Ban information updated successfully!"}, status=status.HTTP_200_OK)

    def put(self, request, org, search_by, criteria, *args, **kwargs):
        qs = self._build_search_queryset(org, search_by, criteria)
        count = qs.count()

        if count == 0:
            return Response({"message": "No matches found."}, status=status.HTTP_404_NOT_FOUND)
        if count > 1:
            return Response(
                {
                    "message": "Multiple matches; cannot update uniquely.",
                    "count": count,
                    "results": BaseDataTableAllShowSerializer(qs, many=True).data[:20],
                },
                status=status.HTTP_409_CONFLICT
            )

        instance = qs.first()
        data = request.data.copy()

        # Diff for audit
        original_data = {f.name: getattr(instance, f.name) for f in instance._meta.fields}

        serializer = BanSaveSerializer(instance, data=data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"message": "Unable to update BAN.", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save()

        change_log = track_model_changes(instance, original_data)
        msg = f"Following fields are updated of account number {instance.accountnumber} : {change_log}"
        saveuserlog(request.user, description=msg)   


        return Response({"message": "Ban updated successfully"}, status=status.HTTP_200_OK)

    def delete(self, request, org, search_by, criteria, *args, **kwargs):
        qs = self._build_search_queryset(org, search_by, criteria)
        count = qs.count()

        if count == 0:
            return Response({"message": "No matches found."}, status=status.HTTP_404_NOT_FOUND)
        if count > 1:
            return Response(
                {
                    "message": "Multiple matches; cannot delete uniquely.",
                    "count": count,
                    "results": BaseDataTableAllShowSerializer(qs, many=True).data[:20],
                },
                status=status.HTTP_409_CONFLICT
            )

        base = qs.first()

        # Follow same linkage logic (uploaded first, then onboarded)
        if base.banOnboarded:
            obj = OnboardBan.objects.get(id=base.banOnboarded.id)
        elif base.banUploaded:
            obj = UploadBAN.objects.get(id=base.banUploaded.id)
        else:
            return Response({"message": "BAN linkage not found."}, status=status.HTTP_400_BAD_REQUEST)

        acc = getattr(obj, "account_number", base.accountnumber)
        obj.delete()
        saveuserlog(request.user, f"account number {acc} deleted successfully.")
        # create_notification(request.user, f"account number {acc} deleted successfully.",request.user.company)
        return Response({"message": f"Ban with account number {base.accountnumber} deleted successfully!"},
                        status=status.HTTP_200_OK)

