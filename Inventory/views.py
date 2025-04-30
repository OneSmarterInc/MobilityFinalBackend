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
from .ser import CompanyShowOnboardSerializer, OrganizationShowOnboardSerializer, BanShowSerializer, OnboardBanshowserializer, BaseDataTableShowSerializer, UploadBANSerializer, UniqueTableShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog
from OnBoard.Ban.models import UploadBAN, OnboardBan, BaseDataTable
# Create your views here.


class InventorySubjectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.designation.name == "Superadmin":
            objs = Company.objects.all()
            onboardbanObjs = BaseDataTable.objects.filter(viewuploaded=None)
            onbanser = BaseDataTableShowSerializer(onboardbanObjs, many=True)
            serializer = CompanyShowOnboardSerializer(objs, many=True)
            all_lines = UniquePdfDataTable.objects.filter(viewuploaded=None)
            lines_Ser = UniqueTableShowSerializer(all_lines, many=True)
            return Response({"data": serializer.data, 'banonboarded':onbanser.data, "lines":lines_Ser.data}, status=status.HTTP_200_OK)
        elif request.user.designation.name == "Admin":
            com = Company.objects.get(Company_name=request.user.company)
            objs = Organizations.objects.filter(company=com)
            allobjs = OnboardBan.objects.all()
            serializer = OrganizationShowOnboardSerializer(objs, many=True)
            onboardbanObjs = BaseDataTable.objects.filter(company=request.user.company).filter(viewuploaded=None)
            onbanser = BaseDataTableShowSerializer(onboardbanObjs, many=True)
            all_lines = UniquePdfDataTable.objects.filter(viewuploaded=None)
            lines_Ser = UniqueTableShowSerializer(all_lines, many=True)
            return Response({"data": serializer.data, 'banonboarded':onbanser.data, "lines":lines_Ser.data}, status=status.HTTP_200_OK)
        try:
            if request.user.designation.name == "Superadmin":
                objs = Company.objects.all()
                serializer = CompanyShowOnboardSerializer(objs, many=True)
                print(serializer.data)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            elif request.user.designation.name == "Admin":
                objs = Organizations.objects.all()
                serializer = OrganizationShowOnboardSerializer(objs, many=True)
                print(serializer.data)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            company = Company.objects.all()
            organization = Organizations.objects.all()
            location = Location.objects.all()
            vendors = Vendors.objects.all()
            company_serializer = CompanygetNameSerializer(company, many=True)
            organization_serializer = OrganizationgetNameSerializer(organization, many=True)
            location_serializer = LocationGetNameSerializer(location, many=True)
            vendor_serializer = VendorNameSerializer(vendors, many=True)

            return Response({
                "message" : "Data fetched successfully!",
                "companies" : company_serializer.data,
                "organizations" : organization_serializer.data,
                "locations" : location_serializer.data,
                "vendors" : vendor_serializer.data,
            }, status=status.HTTP_200_OK)
        except:
            return Response({"message": "Error getting data"}, status=status.HTTP_401_UNAUTHORIZED)
        
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
                company.delete()
                saveuserlog(request.user, f"Company named {id} deleted successfully!")
                return Response({"message": "company deleted successfully!"}, status=status.HTTP_200_OK)
            elif subject == "Organization":
                organization = Organizations.objects.filter(id=id).first()
                organization.delete()
                saveuserlog(request.user, f"Organization named {id} deleted successfully!")
                return Response({"message" : "organization deleted successfully!"}, status=status.HTTP_200_OK)
            elif subject == "Location":
                location = Location.objects.filter(id=id).first()
                location.delete()
                saveuserlog(request.user, f"Location named {id} deleted successfully!")
                return Response({"message" : "Location deleted successfully!"}, status=status.HTTP_200_OK)
            elif subject == "Vendor":
                vendor = Vendors.objects.filter(id=id)
                vendor.delete()
                saveuserlog(request.user, f"Vendor named {id} deleted successfully!")
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
class BanInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org, vendor, ban, *args, **kwargs):
        try:
            orgobject = Organizations.objects.get(Organization_name=org)
            locobj = Location.objects.filter(organization=orgobject)
            vendorobject = Vendors.objects.get(name=vendor)
            banobject = BaseDataTable.objects.filter(viewuploaded=None).get(accountnumber=ban)
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
                
        banlines = UniquePdfDataTable.objects.filter(viewuploaded=None)
        vendorser = VendorGetAllDataSerializer(vendorobject)
        orgser = OrganizationGetAllDataSerializer(orgobject)
        locser = LocationGetAllDataSerializer(locobj, many=True)

        divisions = DivisionNameSerializer(Division.objects.filter(organization=orgobject), many=True)

        allonboards = BaseDataTable.objects.filter(viewuploaded=None).filter(sub_company=org)


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
            obj = BaseDataTable.objects.filter(viewuploaded=None).filter(sub_company=org, vendor=vendor, accountnumber=ban)
        except:
            return Response(
                {"message": "Ban not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        obj = obj[0] 
        print(request.data)

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

        return Response({
            "message": "Ban information updated successfully!"
        }, status=status.HTTP_200_OK)
    
    def put(self, request, org, vendor, ban, *args, **kwargs):
        obj = BaseDataTable.objects.filter(sub_company=org, vendor=vendor, accountnumber=ban)
        if not obj:
            return Response({"message":f"Ban with account number {ban} not found!"},status=status.HTTP_400_BAD_REQUEST)
        data = request.data.copy()
        print(data)
        ser = BanSaveSerializer(obj[0], data=data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response({"message":"Ban updated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"message":f"{str(ser.errors)}"},status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, org, vendor, ban, *args, **kwargs):
        
        base = BaseDataTable.objects.filter(sub_company=org, vendor=vendor, accountnumber=ban)
        if not base:
            return Response({"message":f"Ban with account number {ban} not found!"},status=status.HTTP_400_BAD_REQUEST)
        print(base[0].banOnboarded, base[0].banUploaded)
        if base[0].banOnboarded:
            obj = OnboardBan.objects.get(id=base[0].banOnboarded.id)
        elif base[0].banUploaded:
            obj = UploadBAN.objects.get(id=base[0].banUploaded.id)
        else:
            return Response({"message":f"Ban with account number {ban} not found!"},status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response({"message":f"Ban with account number {ban} deleted successfully!"})
        

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

        mobiles = UniquePdfDataTable.objects.filter(viewuploaded=None).filter(account_number=account)
        mobiles = UniqueTableShowSerializer(mobiles, many=True)

        acc = UploadBAN.objects.filter(account_number=account)[0]
        lines = Lines.objects.filter(account_number=acc)
        lines = LineShowSerializer(lines, many=True)

        return Response({
            "mobiles": mobiles.data,
            "lines": lines.data
        }, status=status.HTTP_200_OK)
    
class MobileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request,account_number, wireless_number=None, *args, **kwargs):
        com = request.GET.get('company')
        sub_com = request.GET.get('sub_company')
        lines = UniquePdfDataTable.objects.filter(viewuploaded=None).filter(account_number=account_number, company=com, sub_company=sub_com)
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
        print(com, sub_com, account_number, wireless_number)
        mainobject = UniquePdfDataTable.objects.filter(viewuploaded=None).filter(company=com, sub_company=sub_com, account_number=account_number,vendor=vendor)
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
                saveuserlog(
                    request.user,
                    f'mobile data of account number {data["account_number"]} added successfully!'
                )
                return Response({
                    "message": f"mobile data of number {data['wireless_number']} added successfully!"
                },status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response({
                    "message": str(serializer.errors)
                },status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
            "message": str(e)
        },status=status.HTTP_400_BAD_REQUEST)

    def put(self, request,account_number,wireless_number, *args, **kwargs):
        obj = UniquePdfDataTable.objects.filter(viewuploaded=None).filter(account_number=account_number, wireless_number=wireless_number)
        if obj:
            obj = obj[0]
        else:
            return Response({
                "message": "Mobile data not found"
            },status=status.HTTP_404_NOT_FOUND)
        try:
            serializer = UniqueTableShowSerializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                saveuserlog(
                    request.user,
                    f'mobile data of account number {account_number} and wireless number {wireless_number} updated successfully!'
                )
                return Response({
                    "message": f"mobile data of number {wireless_number} updated successfully!"
                },status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": str(serializer.errors)
                },status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
            "message": str(e)
        },status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request,account_number,wireless_number, *args, **kwargs):
        try:
            obj = UniquePdfDataTable.objects.filter(viewuploaded=None).filter(account_number=account_number, wireless_number=wireless_number)
            if obj:
                obj = obj[0]
            else:
                return Response({
                    "message": "Mobile data not found"
                },status=status.HTTP_404_NOT_FOUND)
            obj.delete()
            saveuserlog(
                request.user,
                f'mobile data of account number {account_number} and wireless number {wireless_number} deleted successfully!'
            )
            return Response({
                "message": f"mobile data of number {wireless_number} deleted successfully!"
            },status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
            "message": str(e)
        },status=status.HTTP_400_BAD_REQUEST)