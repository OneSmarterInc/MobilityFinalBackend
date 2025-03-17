from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status

from .models import UploadBAN, Lines
from .ser import UploadBANSerializer
from authenticate.views import saveuserlog
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
import json
from ..Organization.models import Organizations
from .ser import EntryTypeShowSerializer
from .uploadSer.ser import CompanyShowSerializer, OrganizationShowuploadSerializer, VendorShowSerializer, BanStatusShowSerializer, BanTypeShowSerializer, InvoiceMethodShowSerializer, PaymentTypeShowSerializer, CostCenterLevelShowSerializer, CostCenterTypeShowSerializer, BanshowSerializer
from ..Company.models import Company
from ..Location.models import Location
from Dashboard.ModelsByPage.DashAdmin import Vendors, EntryType, BanStatus, BanType, InvoiceMethod, PaymentType, CostCenterLevel, CostCenterType
from authenticate.models import PortalUser
import ast
import os
class UploadBANView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            ban = UploadBAN.objects.get(account_number=pk)
            serializer = UploadBANSerializer(ban)
            return Response({"data" : serializer.data }, status=status.HTTP_200_OK)
        else:
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

            bans = UploadBAN.objects.filter(entryType=EntryType.objects.get(name="Master Account"))
            banserializer = BanshowSerializer(bans, many=True)
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
                'bans' : banserializer.data,
                }, status=status.HTTP_200_OK)
        

    def predatatrasform(self, data):
        mutable_data = data.copy()
        mutable_data = {key: (value if value != "" else None) for key, value in mutable_data.items()}
        if mutable_data.get('lines') == 'null':
            print("it is null lines")
            mutable_data['lines'] = []
        lines = mutable_data.pop('lines', [])
        if isinstance(lines, str):
            try:
                lines = json.loads(lines)
            except json.JSONDecodeError:
                return Response({"message": "Invalid JSON format for 'lines'"}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(lines, list): 
            return Response({"message": "'lines' must be a list of dictionaries"}, status=status.HTTP_400_BAD_REQUEST)

        boolean_fields = ["is_it_consolidatedBan", "auto_pay_enabled", "costcenterstatus", "Displaynotesonbillprocessing"]
        for field in boolean_fields:
            if field in mutable_data:
                mutable_data[field] = self.str_to_bool(mutable_data.get(field, False))
        
        return mutable_data, lines
    def post(self, request):
        ban = UploadBAN.objects.filter(account_number=request.data.get('account_number')).first()
        if ban:
            return Response({"message": "Account number already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data
        mutable_data, lines = self.predatatrasform(data)
        print(mutable_data)
        orgobj = Organizations.objects.get(Organization_name=data['organization'])
        try:
            if 'location' in mutable_data and mutable_data['location'] is not None:
                loc = get_object_or_404(Location, site_name=mutable_data.pop('location'), organization=orgobj)
            else:
                loc = None
                mutable_data.pop('location')
            if 'costcenterlevel' in mutable_data and mutable_data['costcenterlevel'] != None:
                costlvl = get_object_or_404(CostCenterLevel, name=mutable_data.pop('costcenterlevel'))
            else:
                costlvl = None
                mutable_data.pop('costcenterlevel')
            if 'costcentertype' in mutable_data and mutable_data['costcentertype'] != None:
                costtype = get_object_or_404(CostCenterType, name=mutable_data.pop('costcentertype'))
            else:
                costtype = None
                mutable_data.pop('costcentertype')
            if 'invoicemethod' in mutable_data and mutable_data['invoicemethod'] != None:
                invoicemethod = get_object_or_404(InvoiceMethod, name=mutable_data.pop('invoicemethod'))
            else:
                invoicemethod = None
                mutable_data.pop('invoicemethod')
            
            upload_ban = UploadBAN.objects.create(
                user_email=get_object_or_404(PortalUser, email=mutable_data.pop('user_email', None)),
                Vendor=get_object_or_404(Vendors, name=mutable_data.pop('Vendor', None)),
                company=get_object_or_404(Company, Company_name=mutable_data.pop('company', None)),
                organization=get_object_or_404(Organizations, Organization_name=mutable_data.pop('organization', None)),
                entryType=get_object_or_404(EntryType, name=mutable_data.pop('entryType', None)),
                location=loc,
                costcenterlevel=costlvl,
                costcentertype=costtype,
                banstatus=get_object_or_404(BanStatus, name=mutable_data.pop('banstatus', None)),
                bantype=get_object_or_404(BanType, name=mutable_data.pop('bantype', None)),
                paymenttype=get_object_or_404(PaymentType, name=mutable_data.pop('paymenttype', None)),
                invoicemethod=invoicemethod,
                masteraccount=mutable_data.pop('masteraccount', None),
                **mutable_data
            )

            saveuserlog(request.user, f"BAN with account number {upload_ban.account_number} created successfully!")

        except Exception as e:
            print(f"Error in BAN creation: {e}")
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print(lines)
        if lines:
            try:
                for line in lines:
                    line = {key: (value if value != "" else None) for key, value in line.items()}

                    line.pop('account_number', None) 
                    if isinstance(line, dict): 
                        lineobj = Lines.objects.create(account_number=upload_ban, **line)
                        lineobj.save()
                        saveuserlog(
                            request.user, 
                            f"Line with account number {upload_ban.account_number} and wireless number {lineobj.wireless_number} created successfully!"
                        )
                    else:
                        print("Skipping invalid line entry:", line)

            except Exception as e:
                print(f"Error in line creation: {e}")
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "BAN created successfully!"}, status=status.HTTP_201_CREATED)
    
    def str_to_bool(self, value):
        return str(value).strip().lower() in ['true','yes']
    
    def put(self, request, pk):
        try:
            ban = UploadBAN.objects.get(id=pk)
            data = request.data
            print(data)
            mutable_data, lines = self.predatatrasform(data)
            print(mutable_data)
            ban.BillingDay = mutable_data['billing_day']
            ban.BillingName = mutable_data['Billing_Name']
            ban.Billing_cycle = mutable_data['Duration']
            ban.paymenttype = PaymentType.objects.filter(name=mutable_data['Payment_Type'])[0] if mutable_data['Payment_Type'] else None
            ban.BillingAdd = mutable_data['Billing_Address']
            ban.BillingCity = mutable_data['billing_city']
            ban.BillingState = mutable_data['billing_state']
            ban.billingZip = mutable_data['billing_zip']
            ban.BillingAtn = mutable_data['billing_attn']
            ban.BillingCountry = mutable_data['billing_country']
            ban.invoicemethod = InvoiceMethod.objects.filter(name=mutable_data['Invoice_Method'])[0] if mutable_data['Invoice_Method'] else None
            ban.entryType = EntryType.objects.filter(name=mutable_data['Entry_type'])[0] if mutable_data['Entry_type'] else None
            ban.Vendor_sub_id = mutable_data['vendor_id']
            ban.bantype = BanType.objects.filter(name=mutable_data['Ban_type'])[0] if mutable_data['Ban_type'] else None
            ban.banstatus = BanStatus.objects.filter(name=mutable_data['Ban_status'])[0] if mutable_data['Ban_status'] else None
            ban.auto_pay_enabled = mutable_data['auto_pay_enabled']
            ban.RemittanceName = mutable_data['Remmitence_name']
            ban.RemittanceAdd = mutable_data['Remidence_Address']
            ban.RemittanceNotes = mutable_data['notes']
            ban.remarks = mutable_data['remarks']
            ban.vendor_alias = mutable_data['vendor_alias']
            ban.vendorCS = mutable_data['cs_number']
            ban.account_password = mutable_data['account_password']
            ban.payor = mutable_data['payor']
            ban.GlCode = mutable_data['gl_code']
            ban.ContractTerms = mutable_data['contract_term']
            ban.ContractNumber = mutable_data['contract_number']
            ban.Services = mutable_data['services']
            ban.AccCharge = mutable_data['account_charge']
            ban.CustomerOfRecord = mutable_data['customer_of_Record']
            ban.PO = mutable_data['po_number']
            ban.POamt = mutable_data['po_amount']
            ban.FoundAcc = mutable_data['foundation_account']
            ban.Displaynotesonbillprocessing = mutable_data['Displaynotesonbillprocessing']
            ban.BillingDate = mutable_data['billingDate']
            ban.save()
            saveuserlog(
                request.user, 
                f"BAN with account number {ban.account_number} updated successfully!"
            )
            return Response(
                {"message": f"BAN with account number {ban.account_number} updated successfully!"}, 
                status=status.HTTP_200_OK
            )
        except UploadBAN.DoesNotExist:
            return Response({"message" : "BAN not found!"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error in BAN update: {e}")
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        # serializer = UploadBANSerializer(ban, data=request.data)

        # if serializer.is_valid():
        #     serializer.save()
        #     saveuserlog(request.user, f"BAN with account number {pk} updated successfully!") 
        #     return Response({"message" : "BAN updated successfully!", "data" : serializer.data}, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        try:
            ban = UploadBAN.objects.get(id=pk)
            acc = ban.account_number
            ban.delete()
            saveuserlog(request.user, f"BAN with account number {acc} deleted successfully!")
            return Response({"message" : "BAN deleted successfully!"}, status=status.HTTP_200_OK)
        except UploadBAN.DoesNotExist:
            return Response({"message" : "BAN not found!"}, status=status.HTTP_404_NOT_FOUND)
        
        
from .models import OnboardBan
from .ser import OnboardBanSerializer, EntryTypeShowSerializer, BillTypeShowSerializer, OrganizationShowOnboardSerializer
from Dashboard.ModelsByPage.DashAdmin import EntryType, BillType
from .models import UploadBAN, MappingObjectBan
class OnboardBanView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            ban = OnboardBan.objects.get(account_number=pk)
            serializer = OnboardBanSerializer(ban)
            return Response({"data" : serializer.data}, status=status.HTTP_200_OK)
        else:
            orgs = Organizations.objects.all()
            orgserializer = OrganizationShowOnboardSerializer(orgs, many=True)
            onboardedbans = OnboardBan.objects.all()
            serializer = OnboardBanSerializer(onboardedbans, many=True)
            etypes = EntryType.objects.all()
            etypeserializer = EntryTypeShowSerializer(etypes, many=True)
            btypes = BillType.objects.all()
            btypeserializer = BillTypeShowSerializer(btypes, many=True)
            return Response({"data" : serializer.data, "organizations": orgserializer.data, "entrytypes" : etypeserializer.data, "billtypes" : btypeserializer.data}, status=status.HTTP_200_OK)
    

    def post(self, request):
        if ('uploadtype' in request.data) and (request.data['uploadtype'] == 'multiple'):

            excel_Data_str = request.data.get('Excelfiles').replace('null', 'None')

            try:
                excel_data = ast.literal_eval(excel_Data_str)
            except (ValueError, SyntaxError) as e:
                print(f"Error in literal_eval: {e}")

            rdd_Data_str = request.data.get('RDDfiles').replace('null', 'None')

            try:
                rdd_Data = ast.literal_eval(rdd_Data_str)
            except (ValueError, SyntaxError) as e:
                print(f"Error in literal_eval: {e}")

            try:
                for i, rd in enumerate(rdd_Data):
                    boolean_fields = ["is_it_consolidatedBan", "baselineCheck"]
                    for field in boolean_fields:
                        rd[field] = self.str_to_bool(rd.get(field, False))
                    rd['uploadBill'] = request.data.get(f'Rddfile_{i}')
                    for k, v in rd.items():
                        if v == '' or v == "":
                            rd[k] = None
                    loc_value = rd.pop('location', None)
                    if loc_value is None:
                        loc = None
                    else:
                        loc = get_object_or_404(Location, site_name=loc_value)
                    master_account_value = rd.pop('masterAccount', None)
                    if master_account_value is None:
                        masteraccount = None 
                    else:
                        masteraccount = get_object_or_404(UploadBAN, account_number=master_account_value)
                    print("master account= ", masteraccount)
                    obj = OnboardBan.objects.create(
                        organization=get_object_or_404(Organizations, Organization_name=rd.pop('organization', None)),
                        vendor=get_object_or_404(Vendors, name=rd.pop('vendor', None)),
                        entryType=get_object_or_404(EntryType, name=rd.pop('entryType', None)),
                        location=loc,
                        masteraccount=masteraccount,
                        uploadBill = rd.pop('uploadBill', None),
                        addDataToBaseline = rd.pop('baselineCheck', False),
                        is_it_consolidatedBan = rd.pop('is_it_consolidatedBan', False)
                    )
                    obj.save()

                for i, ed in enumerate(excel_data):
                    print(ed)
                    boolean_fields = ["is_it_consolidatedBan", "addDataToBaseline"]
                    for field in boolean_fields:
                        ed[field] = self.str_to_bool(ed.get(field, False))
                    ed['uploadBill'] = request.data.get(f'Excelfile_{i}')
                    for k, v in ed.items():
                        if v == '' or v == "":
                            ed[k] = None
                        if k == 'mapping_object':
                            for key, value in v.items():
                                if value == '' or value == "":
                                    v[key] = None
                    print("ed=", ed)
                    master_account_value = ed.pop('masteraccount', None)
                    loc_value = ed.pop('location', None)
                    if loc_value is None:
                        loc = None
                    else:
                        loc = get_object_or_404(Location, site_name=loc_value)
                    if master_account_value is None:
                        masteraccount = None 
                    else:
                        masteraccount = get_object_or_404(UploadBAN, account_number=master_account_value)
                    print("master account= ", masteraccount)
                    obj = OnboardBan.objects.create(
                        organization=get_object_or_404(Organizations, Organization_name=ed.pop('organization', None)),
                        vendor=get_object_or_404(Vendors, name=ed.pop('vendor', None)),
                        entryType=get_object_or_404(EntryType, name=ed.pop('entryType', None)),
                        location=loc,
                        masteraccount=masteraccount,
                        addDataToBaseline = ed.pop('addDataToBaseline', False),
                        is_it_consolidatedBan = ed.pop('is_it_consolidatedBan', False),
                        uploadBill = ed.pop('uploadBill', None),
                    )
                    obj.save()
                    map = ed.pop('mapping_object', None)
                    mobj = MappingObjectBan.objects.create(onboard=obj, **map)
                    mobj.save()

                    mapping_obj = model_to_dict(MappingObjectBan.objects.get(onboard=obj)) or {}
                    print(mapping_obj)
                    if mapping_obj:
                        try:
                            mapping_json = mapping_obj
                        except json.JSONDecodeError:
                            print("")
                            return Response({"message": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)

                        with tempfile.NamedTemporaryFile(delete=False) as temper_file:
                                for chunk in obj.uploadBill.chunks():
                                    temper_file.write(chunk)
                                path = temper_file.name
                        
                        df_csv = pd.read_excel(path)
                        df_csv.columns = df_csv.columns.str.strip()
                        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

                        latest_entry_dict = mapping_json
                        for key, value in latest_entry_dict.items():
                            latest_entry_dict[key] = str(value).replace(' ', '_')
                        column_mapping = {v: k for k, v in latest_entry_dict.items()}
                        filtered_mapping = {key: value for key, value in column_mapping.items() if key != 'NA'}
                                # missing_columns = [col for col in filtered_mapping.keys() if col not in df_csv.columns]
                        for key, value in latest_entry_dict.items():
                            if value == "NA":
                                latest_entry_dict[key] = key
                        columns_to_keep = [col for col in latest_entry_dict.values() if col in df_csv.columns]
                        df_csv = df_csv[columns_to_keep]
                        df_csv.rename(columns=filtered_mapping, inplace=True)
                        print("dffffff",df_csv.columns)
                        account_number = df_csv['account_number'].iloc[0]
                        print("account_number",account_number)
                        from .models import BaseDataTable
                        try:
                            instance = BaseDataTable.objects.get(accountnumber=account_number)
                        except:
                            instance =False    
                        
                        print("instaaaa", instance)
                        
                        if instance is True:
                            return Response(
                                {'message': 'File already exists in the database upload another'}, status=status.HTTP_400_BAD_REQUEST
                            )
                        else:

                            print(obj)

                            ma = None
                            if obj.masteraccount:
                                ma = obj.masteraccount.account_number
                            site = None
                            if obj.location:
                                site = obj.location.site_name

                            buffer_data = json.dumps({'excel_csv_path': obj.uploadBill.path,'company':obj.organization.company.Company_name,'sub_company':obj.organization.Organization_name,'vendor':obj.vendor.name,'entry_type':obj.entryType.name,"mapping_json":mapping_json,'location':site,'master_account':ma,
                            })

                            # if obj.location:
                            #     AllUserLogs.objects.create(
                            #         user_email=request.user.email,
                            #         description=(
                            #             f"User Onboarded excel file for {obj.organization.company.Company_name} - {obj.organization.Organization_name} "
                            #             f"with location {obj.location.site_name} and vendor - {obj.vendor.name}. "
                            #         )
                            #     )
                            # else:
                            #     AllUserLogs.objects.create(
                            #         user_email=request.user.email,
                            #         description=(
                            #             f"User Onboarded excel file for {obj.organization.company.Company_name} - {obj.organization.Organization_name} "
                            #             f"with vendor - {obj.vendor.name}. "
                            #         )
                            #     )

                            from .Background.tasks import process_csv
                            print("process_csv")
                            process_csv(instance=obj, buffer_data=buffer_data)
                saveuserlog(
                    request.user, f"Multiple RDD and Excel uploaded successfully!"
                )
                return Response({"message" :'multiple files uploaded'}, status=status.HTTP_200_OK)

            except Exception as e:
                print(f"Error in creating onboard ban: {e}")
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        mutable_data = request.data.copy()
        mutable_data = {key: (value if value != "" else None) for key, value in mutable_data.items()}
        boolean_fields = ["is_it_consolidatedBan", "addDataToBaseline"]
        for field in boolean_fields:
            mutable_data[field] = self.str_to_bool(mutable_data.get(field, False))
        org = Organizations.objects.get(Organization_name=mutable_data['organization'])
        if 'location' in mutable_data:
            loc = get_object_or_404(Location, site_name=mutable_data['location'], organization=org)
        else:
            loc = None
        if 'billType' in mutable_data:
            btype = get_object_or_404(BillType, name=mutable_data['billType'])
        else:
            btype = None
        master_account_value = mutable_data.pop('masteraccount', None)
        if master_account_value is None:
            masteraccount = None 
        else:
            masteraccount = get_object_or_404(UploadBAN, account_number=master_account_value)
        try:
            obj = OnboardBan.objects.create(
                organization=get_object_or_404(Organizations, Organization_name=mutable_data.pop('organization', None)),
               vendor=get_object_or_404(Vendors, name=mutable_data.pop('vendor', None)),
               
               entryType=get_object_or_404(EntryType, name=mutable_data.pop('entryType', None)),
               location=loc,
               masteraccount=masteraccount,
               uploadBill = mutable_data.pop('uploadBill', None),
               billType = btype,
               addDataToBaseline = mutable_data.pop('addDataToBaseline', False),
               is_it_consolidatedBan = mutable_data.pop('is_it_consolidatedBan', False)
            )
            obj.save()
            if obj.uploadBill.name.endswith('.zip'):
                addon = ProcessZip(obj)
                check = addon.startprocess()
            else:
                addon = ProcessPdf(obj)
                check = addon.startprocess()
                month, year = None, None
                types = []
                buffer_data = json.dumps({'pdf_path': obj.uploadBill.path, 'company_name': obj.organization.company.Company_name, 'vendor_name': obj.vendor.name, 'pdf_filename': obj.uploadBill.name, 'month': month, 'year': year, 'sub_company': obj.organization.Organization_name,'entry_type':obj.entryType.name,'user_email':request.user.email,'types':types,'baseline_check':obj.addDataToBaseline,'location':obj.location.site_name,'master_account':obj.masteraccount.account_number})

                from .Background.tasks import process_pdf_task
                # process_pdf_task(buffer_data)
                # AllUserLogs.objects.create(
                #     user_email=request.user.email,
                #     description=(
                #         f"User uploaded pdf file for {obj.organization.company.Company_name} - {obj.organization.Organization_name}."
                #         f"with vendor name {obj.vendor.name} and account number {obj.masteraccount.account_number}."
                #     )
                # )
            print(check)
            if check['error'] == -1:
                return Response(
                    {"message": f"Problem to add onbaord data, {str(check['message'])}"}, status=status.HTTP_400_BAD_REQUEST
                )

            saveuserlog(request.user, f"Onboard BAN with account number created successfully!")

            return Response(
                {"message": "Onboard BAN created successfully!"}, 
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            print(f"Error in Onboard BAN creation: {e}")
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def str_to_bool(self, value):
        return str(value).strip().lower() == 'true' or str(value).strip().lower() == 'yes'
    def put(self, request, pk):
        ban = OnboardBan.objects.get(account_number=pk)
        serializer = OnboardBanSerializer(ban, data=request.data)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, f"Onboard BAN with account number {pk} updated successfully!") 
            return Response({"message" : "Onboard BAN updated successfully!", "data" : serializer.data}, status=status.HTTP_200_OK)
        return Response({"message" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            ban = OnboardBan.objects.get(account_number=pk)
            ban.delete()
            saveuserlog(request.user, f"Onboard BAN with account number {pk} deleted successfully!")
            return Response({"message" : "Onboard BAN deleted successfully!"}, status=status.HTTP_200_OK)
        except OnboardBan.DoesNotExist:
            return Response({"message" : "Onboard BAN not found!"}, status=status.HTTP_404_NOT_FOUND)
        
from .models import InventoryUpload
from .ser import InventoryUploadSerializer
from .InSer.ser import OrganizationShowSerializer
class InventoryUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            inventory = InventoryUpload.objects.get(account_number=pk)
            serializer = InventoryUploadSerializer(inventory)
            return Response({"data" : serializer.data}, status=status.HTTP_200_OK)
        else:
            orgs = Organizations.objects.all()
            orgserializer = OrganizationShowSerializer(orgs, many=True)
            inventories = InventoryUpload.objects.all()
            serializer = InventoryUploadSerializer(inventories, many=True)
            return Response({"data" : serializer.data,
                             "orgs" : orgserializer.data
                             }, status=status.HTTP_200_OK)
        
    def post(self, request):
        inv = InventoryUpload.objects.filter(organization=Organizations.objects.get(Organization_name=request.data.get('sub_company')), vendor=Vendors.objects.get(name=request.data.get('vendor_name')), ban=UploadBAN.objects.get(account_number=request.data.get('Ban'))).first()
        if inv:
            return Response(
                {"message": "Inventory already exists for this BAN, Vendor, and Sub-Company"},
                status=status.HTTP_409_CONFLICT
            )
        mutable_data = request.data.copy()
        mutable_data = {key: (value if value != "" else None) for key, value in mutable_data.items()}
        try:
            obj = InventoryUpload.objects.create(
               organization=get_object_or_404(Organizations, Organization_name=mutable_data.pop('sub_company', None)),
               vendor=get_object_or_404(Vendors, name=mutable_data.pop('vendor_name', None)),
               ban=get_object_or_404(UploadBAN, account_number=mutable_data.pop('Ban', None)),
               uploadFile = mutable_data.pop('file', None),
            )
 
            obj.save()
            map = request.data.pop('mapping_obj', None)[0]
            map = map.replace('null', 'None')
            map = ast.literal_eval(map)
            for key, value in map.items():
                if value == "" or value == '':
                    map[key] = None
            mobj = MappingObjectBan.objects.create(inventory=obj, **map)
            mobj.save()

            process  = InventoryProcess(instance=obj)
            start, previous_data_log, new_data_log  = process.process_file()
            if start:
                # All users log
                # AllUserLogs.objects.create(
                #     user_email=request.user.email,
                #     description=(
                #         f"User onboarded excel file for {obj.organization.company.Company_name} - {obj.organization.Organization_name} "
                #         f"with account number {obj.ban.account_number} and vendor - {obj.vendor.name}."
                #     ),
                #     previus_data=json.dumps(previous_data_log) if previous_data_log else "",
                #     new_data=json.dumps(new_data_log) if new_data_log else ""
                # )
                saveuserlog(request.user, f"Inventory upload with account number {obj.ban.account_number} created successfully!")

                from .Background.tasks import process_csv
                
                buffer_data = json.dumps({
                    'csv_path': obj.uploadFile.path,
                    'company': obj.organization.company.Company_name,
                    'sub_company': obj.organization.Organization_name,
                    'vendor': obj.vendor.name,
                    'account_number': obj.ban.account_number,
                    'mapping_json': model_to_dict(MappingObjectBan.objects.get(inventory=obj)) or {}
                })
                print(buffer_data)
                print("Starting CSV process...")
                process_csv(instance=obj, buffer_data=buffer_data)

                return Response({"message" : "Inventory uploaded successfully!", "data" : mutable_data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": "Inventory process failed!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            print("inventory post error=", str(e))
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk):
        inventory = InventoryUpload.objects.get(account_number=pk)
        serializer = InventoryUploadSerializer(inventory, data=request.data)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, f"Inventory upload with account number {pk} updated successfully!") 
            return Response({"message" : "Inventory upload updated successfully!", "data" : serializer.data}, status=status.HTTP_200_OK)
        return Response({"message" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            inventory = InventoryUpload.objects.get(account_number=pk)
            inventory.delete()
            saveuserlog(request.user, f"Inventory upload with account number {pk} deleted successfully!")
            return Response({"message" : "Inventory upload deleted successfully!"}, status=status.HTTP_200_OK)
        except InventoryUpload.DoesNotExist:
            print("delete inventory error")
            return Response({"message" : "Inventory upload not found!"}, status=status.HTTP_404_NOT_FOUND)

import tempfile
from .models import UniquePdfDataTable
from django.forms.models import model_to_dict
class InventoryProcess:
    def __init__(self, instance):
        self.instance = instance
        self.file = instance.uploadFile
        self.filename = instance.uploadFile.name
        self.org = instance.organization.Organization_name
        self.company = instance.organization.company.Company_name
        self.ban = instance.ban.account_number
        self.mapping = model_to_dict(MappingObjectBan.objects.get(inventory=self.instance))

    def process_file(self):
        try:
            df_csv = pd.read_excel(BytesIO(self.file.read()))
            df_csv.columns = df_csv.columns.str.strip()

            df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

            # Save column names mapping in Column_mapping_data
            columns_list = df_csv.columns.tolist()
            column_names_str = ','.join(columns_list)

            # Save the uploaded file temporarily for background processing
            with tempfile.NamedTemporaryFile(delete=False) as temper_file:
                for chunk in self.file.chunks():
                    temper_file.write(chunk)
                path = temper_file.name

            # Parse the mapping object and set wireless number column
            wireless_column_name = self.mapping.get('wireless_number', 'wireless_number')

            # Filter unique_pdf_data_table for existing data with the given account number (Ban)
            existing_data = UniquePdfDataTable.objects.filter(account_number=self.ban)

            # Create a dictionary of existing data by wireless number for easy access
            existing_wireless_data = {
                row['wireless_number']: row for row in existing_data.values()
            }

            # Initialize logs for previous and new data
            previous_data_log = []
            new_data_log = []

            for _, new_row in df_csv.iterrows():
                wireless_number = new_row.get(wireless_column_name)
                if wireless_number in existing_wireless_data:
                    # Existing row found, compare each field for changes
                    old_row = existing_wireless_data[wireless_number]
                    updated_fields = {}
                    for field in df_csv.columns:
                        new_value = new_row[field]
                        old_value = old_row.get(field)

                        # Check if the field's new value differs from old value, handle NaT if present
                        if pd.notna(new_value) and new_value != old_value:
                            updated_fields[field] = new_value

                    # If any updates are found, log both previous and updated fields
                    if updated_fields:
                        previous_data_log.append(self.clean_data_for_json(old_row))  # Full old row for reference
                        new_data_log.append(self.clean_data_for_json(updated_fields))  # Only changed fields for new data
                else:
                    # For new wireless numbers, log the entire row in new data
                    new_data_log.append(self.clean_data_for_json(new_row.to_dict()))
                    
            return True, previous_data_log, new_data_log
    
        except Exception as e:
            print("Error occurred during file processing: ", str(e))
            return False, previous_data_log, new_data_log
    
    def clean_data_for_json(self, data):
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, pd.Timestamp):
                cleaned_data[key] = value.isoformat() if not pd.isna(value) else None
            elif pd.isna(value):
                cleaned_data[key] = None
            else:
                cleaned_data[key] = value
        return cleaned_data

import os
import zipfile
from io import BytesIO, StringIO
import pandas as pd
import re
import pdfplumber
from .models import PdfDataTable
class ProcessPdf:
    def __init__(self, request, instance, **kwargs):
        self.instance = instance
        self.file = instance.uploadBill
        if self.file is None:
            return {'message' : 'File not found', 'error' : -1}
        self.path = instance.uploadBill.path
        if not self.path:
            return {'message' : 'File not found', 'error' : -1}
        else:
            self.path = self.path.path
        self.org = instance.organization
        self.company = instance.organization.company
        self.vendor = instance.vendor
        self.entrytype = instance.entryType
        self.masteraccount = instance.masteraccount
        self.consoBan = instance.is_it_consolidatedBan
        self.loc = instance.location
        self.billtype = instance.billType
        self.baseline = instance.addDataToBaseline
        self.vendorList = Vendors.objects.all()
        self.typesList = BillType.objects.all()
        self.types = None
        self.email = request.user.email
        self.month = None
        self.year = None
    def startprocess(self):
        print("start process")
        if self.org:
                self.org = self.org.Organization_name
        else:
            return {'message' : 'Organization not found', 'error' : -1}
        if self.company:
            self.company = self.company.Company_name
        else:
            return {'message' : 'Company not found', 'error' : -1}
        if self.vendor:
            self.vendor = self.vendor.name
        else:
            return {'message' : 'Vendor not found', 'error' : -1}

        if self.entrytype:
            self.entrytype = self.entrytype.name
        else:
            return {'message' : 'Entry Type not found', 'error' : -1}

        if self.masteraccount:
            self.masteraccount = self.masteraccount.account_number
        if self.loc:
            self.loc = self.loc.site_name
        if self.billtype:
            self.billtype = self.billtype.name
        acc_info = None
        bill_date_info = None

        if self.vendor in self.vendorList and 'mobile' in str(self.vendor).lower():
            pass
        elif self.vendor in self.vendorList and str(self.vendor).replace(' ', '').lower().startswith('at'):
            pages_data = []
            with pdfplumber.open(self.path) as pdf:
                num_of_pages = len(pdf.pages)
            if num_of_pages < 999:
                with pdfplumber.open(self.path) as pdf:
                    pages_data = [page.extract_text() for page in pdf.pages[:2]]

                for page_data in pages_data:
                    first_page_data = page_data
                    break

                first_page_data_dict = {
                    "bill_cycle_date": None,
                    "account_number": None
                }

                for line in first_page_data.splitlines():
                    if line.startswith("Issue Date:"):
                        first_page_data_dict["bill_cycle_date"] = line.split(": ")[-1]
                    elif line.startswith("Account Number:"):
                        first_page_data_dict["account_number"] = line.split(": ")[-1]
                acc_info = first_page_data_dict["account_number"]
                bill_date_info = first_page_data_dict["bill_cycle_date"]
        else:
            accounts = []
            dates = []
            duration = []
            bill_date = []
            with pdfplumber.open(self.path) as pdf:
                for page_number in range(2):
                    page = pdf.pages[page_number]
                    text = page.extract_text()
                    lines = text.split('\n')
                    for index, line in enumerate(lines):
                        if line.startswith('InvoiceNumber AccountNumber DateDue'):
                            line = lines[index + 1]
                            items = line.split()
                            del items[3]
                            del items[4]
                            del items[3]
                            date = items[2]
                            account = items[1]
                            dates.append(date)
                            accounts.append(account)

                    match = re.search(r'Quick Bill Summary (\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*-\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b)', text)
                    if match:
                        phone_number = match.group(1)
                        duration.append(phone_number)

                    match = re.search(r'Bill Date (January|February|March|April|May|June|July|August|September|October|November|December) (\d{2}), (\d{4})', text)
                    if match:
                        phone_number = match.group(1)
                        amount = match.group(2)
                        pay = match.group(3)
                        bill_date.append({
                            "phone_number": phone_number,
                            "amount": amount,
                            "pay": pay
                        })

            bill_date1 = [f"{info['phone_number']} {info['amount']} {info['pay']}" for info in bill_date]
            acc_info = accounts[0]
            bill_date_info = bill_date1[0]
        acc_no = acc_info
        bill_date_pdf = bill_date_info
        acc_exists = PdfDataTable.objects.filter(AccountNumber=acc_no)
        bill_date_exists = PdfDataTable.objects.filter(Bill_Date=bill_date_pdf)
        message = ''
        if acc_exists:
            pass
        # storage = FileSystemStorage(location='uploaded_contracts/')
        # filename = storage.save(self.file.name, self.path)
        # path = storage.path(filename)

        return {
            'message': 'Process Done',
            'error': 0,
        }






class ProcessZip:
    def __init__(self, instance, **kwargs):
        self.instance = instance
        self.path = instance.uploadBill
        if not self.path:
            return {'message' : 'File not found', 'error' : -1}
        else:
            self.path = self.path.path
        self.org = instance.organization
        self.company = instance.organization.company
        print(self.company)
        self.vendor = instance.vendor
        self.entrytype = instance.entryType
        self.masteraccount = instance.masteraccount
        self.consoBan = instance.is_it_consolidatedBan
        self.loc = instance.location
        self.billtype = instance.billType
        self.baseline = instance.addDataToBaseline
        self.vendorList = Vendors.objects.all()
        self.typesList = BillType.objects.all()
        self.types = None


    def startprocess(self):
        print("start process")
        try:
            if self.org:
                self.org = self.org.Organization_name
            else:
                return {'message' : 'Organization not found', 'error' : -1}
            if self.company:
                self.company = self.company.Company_name
                print("company====", self.company)
            else:
                return {'message' : 'Company not found', 'error' : -1}
            if self.vendor:
                self.vendor = self.vendor.name
            else:
                return {'message' : 'Vendor not found', 'error' : -1}

            if self.entrytype:
                self.entrytype = self.entrytype.name
            else:
                return {'message' : 'Entry Type not found', 'error' : -1}

            if self.masteraccount:
                self.masteraccount = self.masteraccount.account_number
            if self.loc:
                self.loc = self.loc.site_name
            if self.billtype:
                self.billtype = self.billtype.name

            if self.path.endswith('.zip'):
                data_base, data_pdf,detailed_df,required_df = self.extract_rdd_data(self.path,self.org)
                data_base['company'] = self.company
                data_base['Entry_type'] = self.entrytype
                data_base['vendor'] = self.vendor
                data_base['sub_company'] = self.org
                data_base['location'] = self.loc
                data_base['master_account'] = self.masteraccount
                data_base['Total_Current_Charges'] = list(required_df['Total Current Charges'])[0]
                data_base['Remidence_Address'] = list(required_df['Remittance Address'])[0]
                data_base['Billing_Name'] = list(required_df['Bill Name'])[0]
                data_base['Total_Amount_Due'] = list(required_df['Total Amount Due'])[0]

                v, t = None, None
                category_data = data_pdf.to_dict(orient='records')
                for entry in category_data:
                    entry['company'] = self.company
                    entry['vendor'] = self.vendor
                self.save_to_pdf_data_table(data_pdf, v, t)
                print("saved to pdf data table")

                for entry in data_pdf.to_dict(orient="records"):
                    entry['company'] = self.company
                    entry['vendor'] = self.vendor
                acc_no = data_base['accountnumber']
                bill_date = data_base['bill_date']


                from .models import BaseDataTable
                if BaseDataTable.objects.filter(accountnumber=acc_no, bill_date=bill_date).exists():
                    return {'message' : f'Bill already exists for account number {acc_no} and bill date {bill_date}', 'error' : -1}
                else:
                    obj = BaseDataTable.objects.create(banOnboarded=self.instance, **data_base)
                    print("saved to base data table")
                    obj.save()
                print('done')
                self.save_to_batch_report(data_base, self.vendor)
                print('saved to batch report')
                self.save_to_unique_pdf_data_table(detailed_df, v, t)
                print('saved to unique pdf data table')
                from collections import defaultdict
                wireless_data = defaultdict(lambda: defaultdict(dict))
                tmp_df = detailed_df
                tmp_df.rename(columns={'Item Category':'Item_Category','Item Description':'Item_Description','Wireless Number':'Wireless_number'},inplace=True)
                for idx, row in tmp_df.iterrows():
                            wireless_number = row['Wireless_number']
                            item_category = row['Item_Category']
                            item_description = row['Item_Description']
                            charges = row['Charges']
                            if pd.notna(item_category) and pd.notna(item_description) and pd.notna(charges):
                                wireless_data[wireless_number][item_category][item_description] = charges
                result_list = [dict(wireless_data)]
                udf = pd.DataFrame(data_pdf)
                wireless_numbers = []
                charges_objects = []
                for entry in result_list:
                        for number, charges in entry.items():
                            wireless_numbers.append(number)
                            charges_objects.append(json.dumps(charges))  # Convert dictionary to JSON string for storage

                    # Create the DataFrame with two columns: Wireless_number and Charges_Object
                obj_df = pd.DataFrame({
                        'Wireless_number': wireless_numbers,
                        'category_object': charges_objects
                    })
                udf.rename(columns={'wireless_number':'Wireless_number'},inplace=True)
                category_obj_df = pd.merge(udf,obj_df,on='Wireless_number',how='left')
                category_obj_df['category_object'] = category_obj_df['category_object'].apply(
                lambda x: {"NAN": "NAN"} if pd.isna(x) or x == '' else x
                )
                category_data = category_obj_df.to_dict(orient='records')
                for entry in category_data:
                    entry['company'] = self.company
                    entry['vendor'] = self.vendor
                if self.baseline:
                    self.save_to_baseline_data_table(category_data, self.vendor, self.types)
                    print("saved to baseline data table")
                return {'message' : 'RDD uploaded successfully!', 'error' : 1}
        except Exception as e:
            print(f'Error occurred while processing zip file: {str(e)}')
            return {'message' : f'Error occurred while processing zip file: {str(e)}', 'error' : -1}
    
            
    def save_to_baseline_data_table(self, data, vendor, types):
        print("save to baseline data table")
        data_df = pd.DataFrame(data)
        if (vendor in self.vendorList and 'mobile' in str(vendor).lower()) and (types in self.typesList and 'first' in str(types).lower()):
            column_mapping = {
                'Wireless_number': 'wireless_number',
                'Recurring Charges': 'monthly_charges',
                'Usage Charges': 'usage_and_purchase_charges',
                'Other Charges': 'surcharges_and_other_charges_and_credits',
                'Third-party Charges': 'third_party_charges_includes_tax',
                'Taxes & Surcharges': 'taxes_governmental_surcharges_and_fees',
                'Total Current Charges': 'total_charges',
                'Data Usage (KB)': 'data_usage',
                'Data Usage (MB)': 'data_usage',
                'User name': 'user_name',
                'Foundation account': 'foundation_account',
                'item category': 'item_category',
                'item description': 'item_description',
                'bill_date': 'bill_date',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company',
                'category_object':'category_object',
                'account_number':'account_number'
            }

            # Drop any columns not in the mapping
            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            # Rename the columns
            data_df = df_filtered.rename(columns=column_mapping)
        elif (vendor in self.vendorList and 'mobile' in str(vendor).lower()) and (types in self.typesList and 'second' in str(types).lower()):
            column_mapping = {
                'Wireless Number': 'wireless_number',
                'User Name': 'user_name',
                'Plans': 'plans',
                'Usage charges': 'usage_and_purchase_charges',
                'Equipment': 'equipment_charges',
                'Taxes & Fees': 'taxes_governmental_surcharges_and_fees',
                'Total': 'total_charges',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company'
            }

            # Drop columns not in the mapping
            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            # Rename the columns based on the mapping
            data_df = df_filtered.rename(columns=column_mapping)
        
        if 'Page Number' in data_df.columns:
            data_df.drop(columns=['Page Number','Monthly charges Add-ons','Billing_Name','Billing_Address', 'Remidence_Addresss','Activity since last bill'],inplace=True)
        data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account Number':'account_number_y','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data_df.columns = data_df.columns.str.replace('&', 'and')
        data_df.columns = data_df.columns.str.replace('-', ' ')
        data_df.columns = data_df.columns.str.replace(' ', '_')
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)

        data = data_df.to_dict(orient='records')

        import json
        from .models import BaselineDataTable
        objects_to_create = []

        for item in data:

            # Convert dictionary values to JSON strings where needed
            processed_item = {key: json.dumps(value) if isinstance(value, dict) else value for key, value in item.items()}
            processed_item.pop('company')
            processed_item.pop('vendor')
            
            # Create Django model instance
            objects_to_create.append(BaselineDataTable(banOnboarded=self.instance, **processed_item, company=self.company, vendor=self.vendor))

        # Bulk insert records
        BaselineDataTable.objects.bulk_create(objects_to_create, ignore_conflicts=True)


    def save_to_unique_pdf_data_table(self, data, vendor,types):
        print("save to unique_pdf_data_table")
        data_df = pd.DataFrame(data)
        if (vendor in self.vendorList and 'mobile' in str(vendor).lower()) and (types in self.typesList and 'first' in str(types).lower()):
            column_mapping = {
                'wireless number': 'wireless_number',
                'Recurring Charges': 'monthly_charges',
                'Usage Charges': 'usage_and_purchase_charges',
                'Other Charges': 'surcharges_and_other_charges_and_credits',
                'Third-party Charges': 'third_party_charges_includes_tax',
                'Taxes & Surcharges': 'taxes_governmental_surcharges_and_fees',
                'Total Current Charges': 'total_charges',
                'Data Usage (KB)': 'data_usage',
                'Data Usage (MB)': 'data_usage',
                'User name': 'user_name',
                'Foundation account': 'foundation_account',
                'item category': 'item_category',
                'item description': 'item_description',
                'bill_date': 'bill_date',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company',
                'account_number':'account_number'
            }
            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            # Rename the columns
            data_df = df_filtered.rename(columns=column_mapping)
        elif (vendor in self.vendorList and 'mobile' in str(vendor).lower()) and (types in self.typesList and'second' in str(types).lower()):
            column_mapping = {
                'Wireless Number': 'wireless_number',
                'User Name': 'user_name',
                'Plans': 'plans',
                'Usage charges': 'usage_and_purchase_charges',
                'Equipment': 'equipment_charges',
                'Taxes & Fees': 'taxes_governmental_surcharges_and_fees',
                'Total': 'total_charges',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company'
            }

            # Drop columns not in the mapping
            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            # Rename the columns based on the mapping
            data_df = df_filtered.rename(columns=column_mapping)
        if 'Page Number' in data_df.columns:
            data_df.drop(columns=['Page Number','Monthly charges Add-ons','Billing_Name','Billing_Address', 'Remidence_Addresss','Activity since last bill'],inplace=True)
        data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account Number':'account_number_y','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data_df.columns = data_df.columns.str.replace('&', 'and')
        data_df.columns = data_df.columns.str.replace('-', ' ')
        data_df.columns = data_df.columns.str.replace(' ', '_')
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data = data_df.to_dict(orient='records')
        
        from .models import UniquePdfDataTable

        data = self.map_json_to_model(data)
        print(data)
        model_fields = {field.name for field in UniquePdfDataTable._meta.fields}
        objects_to_create = [
            UniquePdfDataTable(banOnboarded=self.instance, **{key: value for key, value in item.items() if key in model_fields})
            for item in data
        ]
        # Bulk insert records
        UniquePdfDataTable.objects.bulk_create(objects_to_create, ignore_conflicts=True)
    def map_json_to_model(self, data):
        KEY_MAPPING = {
            "account_number_y": "account_number",
            "Wireless_Number": "wireless_number",
            "User_Name": "user_name",
            "Item_Description": "plans",
            "Cost_Center": "cost_center",
            "Item_Category": "account_charges_and_credits", 
            "sub_company": "sub_company",
            "Charges": "total_charges",
        }
        mapped_data = []
        for entry in data:
            mapped_entry = {}

            for key, value in entry.items():
                mapped_key = KEY_MAPPING.get(key, key)  
                mapped_entry[mapped_key] = value if pd.notna(value) else "NaN"

            mapped_data.append(mapped_entry)

        return mapped_data
    def save_to_batch_report(self, data, vendor):
        print("save to batch report")
        try:
            if (vendor in self.vendorList) and (('a' and 't') in str(vendor).lower()):
                return None
            if (vendor in self.vendorList) and ('mobile' in str(vendor).lower()):
                temp = data
                temp_fig = data
            else:
                temp = data[0]
                temp_fig = data[0]
            
            bill_date = temp['bill_date']
            from datetime import datetime
            try:
                date_object = datetime.strptime(bill_date, '%B %d %Y')
                formatted_date = date_object.strftime('%m/%d/%Y')
                temp_fig["bill_date"] = formatted_date
            except:
                try:
                    date_obj = datetime.strptime(bill_date, '%b %d, %Y')
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    temp_fig["bill_date"] = formatted_date
                except:
                    temp_fig['bill_date'] = 'NA'
            
            try:
                if temp["Date_Due"] != "Past":
                    date_due = temp["Date_Due"]
                    date_object_short_year = datetime.strptime(date_due, '%m/%d/%y')
                    formatted_date_long_year = date_object_short_year.strftime('%m/%d/%Y')
                    temp_fig["Date_Due"] = formatted_date_long_year
            except:
                temp_fig["Date_Due"] = 'NA'
            
            remittenceAddress = temp['Remidence_Address']
            parts = remittenceAddress.split(',')

            addresscity = parts[0].split(' ')
            address = f"{addresscity[0]} {addresscity[1]} {addresscity[2]}"
            city = addresscity[4]
            temp_fig["Vendor_City"] = city
            statezip = parts[1].strip().split(' ')
            state = statezip[0]
            temp_fig["Vendor_State"] = state
            temp_fig['Remidence_Address'] = address
            zip_code = statezip[1]
            temp_fig["Vendor_Zip"] = zip_code
        
        except:
            if (vendor in self.vendorList) and (('a' and 't') in str(vendor).lower()):
                temp = data
                temp_fig = data
            else:
                temp = data
                temp_fig = data
            
            bill_date = temp['bill_date']
            try:
                date_object = datetime.strptime(bill_date, '%B %d %Y')
                formatted_date = date_object.strftime('%m/%d/%Y')
                temp_fig['bill_date'] = temp_fig.pop('bill_date')
                temp_fig["bill_date"] = formatted_date
            except:
                try:
                    date_obj = datetime.strptime(bill_date, '%b %d, %Y')
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    temp_fig['bill_date'] = temp_fig.pop('bill_date')
                    temp_fig["bill_date"] = formatted_date
                except:
                    temp_fig['bill_date'] = temp_fig.pop('bill_date')
                    temp_fig['bill_date'] = 'NA'

            try:
                if temp["date_due"] != "Past":
                    date_due = temp["date_due"]
                    date_object_short_year = datetime.strptime(date_due, '%m/%d/%y')
                    formatted_date_long_year = date_object_short_year.strftime('%m/%d/%Y')
                    temp_fig['Date_Due'] = temp_fig.pop('date_due')
                    temp_fig["Date_Due"] = formatted_date_long_year
            except:
                temp_fig['Date_Due'] = temp_fig.pop('date_due')
                temp_fig["Date_Due"] = 'NA'

            temp_fig['AccountNumber'] = temp_fig.pop('accountnumber')
            temp_fig['InvoiceNumber'] = temp_fig.pop('invoicenumber')
            temp_fig['Total_Charges'] = temp_fig.pop('total_charges')
            temp_fig['Remidence_Address'] = 'NA'
            temp_fig['Billing_Name'] = 'NA'
            temp_fig["Vendor_City"] = 'NA'
            temp_fig["Vendor_State"] = 'NA'
            temp_fig["Vendor_Zip"] = 'NA'
        key_mapping = {
            'Date_Due': 'Due_Date',
            'AccountNumber': 'Customer_Vendor_Account_Number',
            'InvoiceNumber': 'Invoice_Number',
            'bill_date': 'Invoice_Date',
            'Remidence_Address': 'Vendor_Address_1',
            'Billing_Name': 'Cust_Id',
            'Total_Charges': 'Net_Amount',
            'vendor': 'Vendor_Name_1',
            'company_name': 'company',
            'Vendor_City': 'Vendor_City',
            'Vendor_State': 'Vendor_State',
            'Vendor_Zip': 'Vendor_Zip'
        }
        fields_to_remove = [
            'Website',
            'Duration',
            'pdf_path',
            'pdf_filename',
            'Billing_Address',
            'Client_Address',
            'foundation_account'
        ]

        for field in fields_to_remove:
            if field in temp_fig:
                del temp_fig[field]

        renamed_data = {key_mapping.get(key, key): value for key, value in temp_fig.items()}

        from .models import BatchReport


        existing_record = BatchReport.objects.filter(
            Customer_Vendor_Account_Number=renamed_data['Customer_Vendor_Account_Number'],
            company=renamed_data['company'],
            Vendor_Name_1=renamed_data['Vendor_Name_1'],
            Invoice_Date=renamed_data['Invoice_Date']
        ).first()

        try:
            batch_vendor = vendor
            if (vendor in self.vendorList) and (('a' and 't') in str(vendor).lower()):
                batch_vendor = 'ATT'
            elif (vendor in self.vendorList) and ('verizon' in str(vendor).lower()):
                batch_vendor = 'VER'
            entered_vendor_zip = zip_code
            entered_vendor_state = state
            entered_vendor_city = city

            count_matches = BatchReport.objects.filter(
                Vendor_Zip=entered_vendor_zip,
                Vendor_State=entered_vendor_state,
                Vendor_City=entered_vendor_city
            )

            result = count_matches.first()

            count_matches = result[0]

            if count_matches > 0:
                max_location_code_entry = (
                    BatchReport.objects
                    .filter(Vendor_Zip=entered_vendor_zip, Vendor_State=entered_vendor_state, Vendor_City=entered_vendor_city)
                    .exclude(Location_Code__isnull=True)  # Exclude null values to avoid errors
                    .order_by('-Location_Code')  # Sorting to get the highest value
                    .values_list('Location_Code', flat=True)  # Get only the Location_Code column
                    .first()
                )

                # Extract the numeric portion after the first three characters
                if max_location_code_entry:
                    max_numeric_part = max_location_code_entry[3:]  # Extract the numeric part
                    new_numeric_part = str(int(max_numeric_part) + 1).zfill(3)  # Increment and pad with leading zeros
                else:
                    new_numeric_part = "001"

                # Generate the new Location_Code
                new_location_code = f"{batch_vendor}{new_numeric_part}"

                # Update records with the new Location_Code
                BatchReport.objects.filter(
                    Vendor_Zip=entered_vendor_zip, Vendor_State=entered_vendor_state, Vendor_City=entered_vendor_city
                ).update(Location_Code=new_location_code)

                print("Location code assigned/updated for the entered vendor-zip:", new_location_code)
            else:
                print("The entered vendor-zip number does not exist in the database.")
        except:
            pass

        # Check if the record exists
        existing_data = BatchReport.objects.filter(
            Customer_Vendor_Account_Number=renamed_data['Customer_Vendor_Account_Number'],
            company=renamed_data['company'],
            Vendor_Name_1=renamed_data['Vendor_Name_1']
        ).first()

        if existing_data:
            # Update existing record
            existing_data.Due_Date = renamed_data['Due_Date']
            existing_data.Invoice_Number = renamed_data['Invoice_Number']
            existing_data.Invoice_Date = renamed_data['Invoice_Date']
            existing_data.Cust_Id = renamed_data['Cust_Id']
            existing_data.Net_Amount = renamed_data['Net_Amount']
            existing_data.save()
        else:
            new_entry = BatchReport.objects.create(banOnboarded=self.instance, **renamed_data)

            if 'new_location_code' in locals() and new_location_code:
                BatchReport.objects.filter(
                    Vendor_Zip=entered_vendor_zip, Vendor_State=entered_vendor_state, Vendor_City=entered_vendor_city
                ).update(Location_Code=new_location_code)

    def save_to_pdf_data_table(self, data, vendor, types):
        print("save to pdf data table")
        data_df = pd.DataFrame(data)
        print('in saves B')
        if ((vendor in self.vendorList) and ('mobile' in str(vendor).lower())) and ((types in self.typesList) and ('first' in str(types).lower())):
            column_mapping = {
                'wireless number': 'Wireless_number',
                'User name': 'User_name',
                'Invoice number': 'Group_number',
                'Recurring Charges': 'Monthly_Charges',
                'Usage Charges': 'Usage_and_Purchase_Charges',
                'Other Charges': 'Surcharges_and_Other_Charges_and_Credits',
                'Taxes & Surcharges': 'Taxes_Governmental_Surcharges_and_Fees',
                'Total Current Charges': 'Total_Charges',
                'Data Usage (KB)': 'Data_Usage',
                'item category': 'item_category',
                'item description': 'item_description',
                'Foundation account': 'foundation_account',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company'
            }
            data_df = data_df.rename(columns=column_mapping)
            data_df = data_df[[col for col in data_df.columns if col in column_mapping.values()]]
        elif vendor in self.vendorList and 'mobile' in str(vendor).lower() and types in self.typesList and 'second' in str(types).lower():
            column_mapping = {
                'Wireless Number': 'Wireless_number',
                'User Name': 'User_name',
                'Plans': 'Plans',
                'Usage charges': 'Usage_and_Purchase_Charges',
                'Equipment': 'Equipment_Charges',
                'Taxes & Fees': 'Taxes_Governmental_Surcharges_and_Fees',
                'Total': 'Total_Charges',
                'company': 'company',
                'vendor': 'vendor',
                'sub_company': 'sub_company'
            }

            df_filtered = data_df[[col for col in data_df.columns if col in column_mapping]]

            data_df = df_filtered.rename(columns=column_mapping)

        if 'Page Number' in data_df.columns:
            data_df.drop(columns=['Page Number','Monthly charges Add-ons','Billing_Name','Billing_Address', 'Remidence_Addresss','Activity since last bill'],inplace=True)
        data_df.rename(columns={'Monthly charges Plan':'monthly_charges',"Monthly charges Equipment":'equipment_charges','Company fees & surcharges':'surcharges_and_other_charges_and_credits','Government fees & taxes':'taxes_governmental_surcharges_and_fees','Total':'total_charges','Account_number':'Account_number','Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data_df.columns = data_df.columns.str.replace('&', 'and')
        data_df.columns = data_df.columns.str.replace('-', ' ')
        data_df.columns = data_df.columns.str.replace(' ', '_')
        data_df.rename(columns={'Voice_Plan_Usage_':"Voice_Plan_Usage"},inplace=True)
        data = data_df.to_dict(orient='records')
        from .models import PdfDataTable
        for item in data:
            if 'company' in item:
                item.pop('company')
            if 'vendor' in item:
                item.pop('vendor')
            try:
                obj = PdfDataTable.objects.create(banOnboarded=self.instance, **item, company=self.company, vendor=self.vendor)
                obj.save()
            except Exception as e:
                print(f'Error saving to database: {e}')
                return {'error':-1, 'message':f'{str(e)}'}
    
    def save_to_base_data_table(self, data):
        print("save to base data table")
        from .models import BaseDataTable
        objects_to_create = [BaseDataTable(banOnboarded=self.instance, **item) for item in data]

        BaseDataTable.objects.bulk_create(objects_to_create, ignore_conflicts=True)


    def extract_rdd_data(self, filepath, organization):
        print("extract rdd data")
        extract_dir = 'Bills/media/extracted_files'
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipfile:
            return {'message' : 'Invalid zip file', 'error' : -1}
        except Exception as e:
            print("Error extracting rdd data=", str(e))
            return {'message' : str(e), 'error' : -1}
        
        relevant_files = [
            os.path.join(root, file)
            for root, _, files in os.walk(extract_dir)
            for file in files if file.endswith('.txt')
        ]
        for filepath in relevant_files:
            if 'Account & Wireless Summary' in filepath:
                database, datapdf = self.process_desired_file1(filepath, organization)
            elif 'Acct & Wireless Charges Detail Summary' in filepath:
                detailed_df = self.process_desired_file2(filepath, organization)
            elif 'AccountSummary' in filepath:
                required_df = self.process_account_summary(filepath, organization)
        self.cleanup_extracted_files(extract_dir)
        return database, datapdf, detailed_df, required_df
    
    def process_desired_file1(self, filepath, organization):
        print("process desired file 1")
        with open(filepath, 'r') as file:
            file_data = file.read()
            df = pd.read_csv(StringIO(file_data), sep='\t')
            def convert_column_name(column_name):
                return column_name.lower().replace(' ', '_')
            df.columns = df.columns.map(convert_column_name)
            required_columns = ['bill_cycle_date', 'account_number', 'date_due',
            'invoice_number', 'bill_period', 'wireless_number', 'user_name',
            'cost_center', 'your_calling_plan',
            'account_charges_and_credits', 'monthly_charges',
            'usage_and_purchase_charges', 'equipment_charges',
            'total_surcharges_and_other_charges_and_credits',
            'taxes,_governmental_surcharges_and_fees', 'third_party_charges',
            'total_charges','voice_plan_usage', 'messaging_usage']
            required_df = df[required_columns].copy()
            column_mapping = {
                'bill_cycle_date': 'bill_date',
                'bill_period': 'duration',
                'your_calling_plan':'plans',
                'invoice_number':'invoicenumber',
                'account_number':'accountnumber',
                "total_surcharges_and_other_charges_and_credits":"surcharges_and_other_charges_and_credits",
                'taxes,_governmental_surcharges_and_fees':'taxes_governmental_surcharges_and_fees',
                'third_party_charges':'third_party_charges_includes_tax'
            }
            required_df.rename(columns=column_mapping,inplace=True)
            # conn = sqlite3.connect('db.sqlite3')
            base_data_df = required_df.iloc[1][['bill_date', 'accountnumber', 'date_due',
            'invoicenumber', 'duration','total_charges']].copy()
            acc_mapping = {'accountnumber':'account_number'}
            required_df.rename(columns=acc_mapping,inplace=True)
            # base_data_df.to_sql('myapp_base_data_table',conn,if_exists='replace', index=False)
            pdf_data_df = required_df[['account_number','wireless_number','user_name','plans','cost_center',
            'account_charges_and_credits', 'monthly_charges',
            'usage_and_purchase_charges', 'equipment_charges',
            'surcharges_and_other_charges_and_credits',
            'taxes_governmental_surcharges_and_fees', 'third_party_charges_includes_tax',
            'total_charges','voice_plan_usage', 'messaging_usage']].copy()
            # pdf_data_df.to_sql('myapp_pdf_data_table',conn,if_exists='replace', index=False)
            # pdf_data_df.to_sql('myapp_unique_pdf_data_table',conn,if_exists='replace', index=False)
            # conn.close()
            pdf_data_df['sub_company'] = organization
            return base_data_df,pdf_data_df
    
    def process_desired_file2(self, filepath, organization):
        print("process desired file 2")
        with open(filepath, 'r') as file:
            file_data = file.read()
            df = pd.read_csv(StringIO(file_data), sep='\t')
            df.rename(columns={'Cost':'Charges'},inplace=True)
            detailed_df = df
            detailed_df['sub_company'] = organization
            return detailed_df
        
    def process_account_summary(self, filepath, organization):
        print("process account summary")
        with open(filepath, 'r') as file:
            file_data = file.read()
            vdf = pd.read_csv(StringIO(file_data), sep='\t')
            vdf['sub_company'] = organization
            return vdf

    def cleanup_extracted_files(self, directory):
        print("cleanup extracted files")
        for root, dirs, files in os.walk(directory):
            for file in files:
                os.remove(os.path.join(root, file))
        os.rmdir(directory)
    
