from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from OnBoard.Organization.models import Organizations
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, BaselineDataTable, OnboardBan
from .ser import showOrganizationSerializer, showBanSerializer, vendorshowSerializer, basedatahowSerializer, paytypehowSerializer, uniquepdftableSerializer, BaselinedataSerializer, BaselineDataTableShowSerializer, showaccountbasetable, BaselineWithOnboardedCategorySerializer,showbaselinenotesSerializer
from Dashboard.ModelsByPage.DashAdmin import Vendors, PaymentType
from ..models import ViewUploadBill, PaperBill

class ViewBill(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        self.basedata = None
        self.uniquedata = None
        self.baseaccounts = None

    def get(self, request, *args, **kwargs):
        objs = Organizations.objects.all()
        ser = showOrganizationSerializer(objs, many=True)
        vendors = vendorshowSerializer(Vendors.objects.all(), many=True)
        paytypes = paytypehowSerializer(PaymentType.objects.all(), many=True)
        
        
        org = request.GET.get("sub_company",None)
        if org:
            self.uniquedata = uniquepdftableSerializer(UniquePdfDataTable.objects.filter(sub_company=org).filter(banOnboarded=None,banUploaded=None), many=True)
            self.baseaccounts = showaccountbasetable(BaseDataTable.objects.filter(sub_company=org).filter(viewuploaded=None, viewpapered=None), many=True)
            self.basedata = basedatahowSerializer(BaseDataTable.objects.filter(sub_company=org).filter(banOnboarded=None,banUploaded=None), many=True)
        return Response({
            "data" : ser.data,
            "vendors" : vendors.data,
            "basedata" : self.basedata.data if self.basedata else None,
            "paytypes" : paytypes.data,
            "uniquedata" : self.uniquedata.data if self.uniquedata else None,
            "baseaccounts": self.baseaccounts.data if self.baseaccounts else None

        }, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        pass
    def put(self, request, pk, *args, **kwargs):
        try:
            obj = BaseDataTable.objects.get(id=pk)
        except BaseDataTable.DoesNotExist:
            return Response({"message": "Base Data not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        print(request.data)
        if request.data['type'] == 'change-payment':
            obj.paymentType = request.data['paymentType']
            saveuserlog(
                request.user, "Changed payment type to " + request.data['paymentType'] + " for Base Data with ID: " + str(pk)
            )
        elif request.data['type'] == 'change-status':
            obj.billstatus = request.data['status']
            saveuserlog(
                request.user, "Changed bill status to " + request.data['status'] + " for Base Data with ID: " + str(pk)
            )
        elif request.data['type'] == 'change-check':
            obj.Check = request.data['check']
            saveuserlog(
                request.user, "Changed check to " + request.data['check'] + " for Base Data with ID: " + str(pk)
            )
        elif request.data['type'] == 'add-summaryfile':
            obj.summary_file = request.data['file']
            saveuserlog(
                request.user, "Added summary file for Base Data with ID: " + str(pk)
            )
        else:
            return Response(
                {"message": "Invalid request type."},
                status=status.HTTP_400_BAD_REQUEST
            )
        obj.save()
        
        return Response({
            "message": "Data successfully Updated!"
        }, status=status.HTTP_200_OK)
    
    def delete(self, request,pk, *args, **kwargs):
        try:
            obj = BaseDataTable.objects.get(id=pk)
        except BaseDataTable.DoesNotExist:
            return Response({"message": "Base Data not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        acc = obj.account_password
        bd = obj.bill_date
        if obj.viewuploaded:
            main_obj = ViewUploadBill.objects.get(id=obj.viewuploaded.id)
            main_obj.delete()
        if obj.viewpapered:
            main_obj = PaperBill.objects.get(id=obj.viewpapered.id)
            main_obj.delete()
        else:
            obj.delete()
        saveuserlog(request.user, f"Bill of account number {acc} and bill date {bd} deletec successfully!")
        return Response({"message": "Bill deleted successfully deleted!"}, status=status.HTTP_200_OK)

from datetime import datetime
class ViewBillBaseline(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        sub_company = request.GET.get('sub_company')
        vendor = request.GET.get('vendor')
        account_number = request.GET.get('account_number')
        date = request.GET.get('bill_date')
        # formatted_date = datetime.strptime(date, "%B %d %Y").date()
        # print(formatted_date)
        objs = BaselineDataTable.objects.filter(banOnboarded=None,banUploaded=None).filter(vendor=vendor, account_number=account_number, sub_company=sub_company, bill_date=date).filter(is_draft=False, is_pending=False)
        base_obj = BaseDataTable.objects.filter(banUploaded=None, banOnboarded=None).filter(sub_company=sub_company, vendor=vendor, accountnumber=account_number, bill_date=date).first()
        base_ser = showbaselinenotesSerializer(base_obj)
        wireless_numbers = objs.values_list('Wireless_number', flat=True)
        Onboardedobjects = BaselineDataTable.objects.filter(
            viewuploaded=None,
            viewpapered=None,
            vendor=vendor,
            account_number=account_number,
            sub_company=sub_company,
            Wireless_number__in=wireless_numbers
        )
        print(base_ser.data)
        serializer = BaselinedataSerializer(objs, many=True, context={'onboarded_objects': Onboardedobjects})
        return Response({"data": serializer.data, "base_data":base_ser.data}, status=status.HTTP_200_OK)
    def put(self, request, pk, *args, **kwargs):
        
        try:
            obj = BaselineDataTable.objects.filter(id=pk)
        except BaselineDataTable.DoesNotExist:
            return Response({"message": "Baseline Data not found"}, status=status.HTTP_404_NOT_FOUND)
        obj = obj[0]
        action = request.GET.get('action') or request.data.get('action')
        if action == "update-category":
            cat = request.data.get('category')
            print(cat)
            obj.category_object = cat
        elif action == "is_draft":
            obj.is_draft = True
            obj.is_pending = False
        elif action == "is_pending":
            obj.is_draft = False
            obj.is_pending = True
        else:
            return Response({"message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        obj.save()
        allobjs = BaselineDataTableShowSerializer(BaselineDataTable.objects.filter(viewuploaded=obj.viewuploaded, is_pending=False, is_draft=False), many=True)
        saveuserlog(
            request.user,
            f"Baseline with account number {obj.account_number} and invoice number {obj.Wireless_number} Updated with Action: {action}"
        )
        return Response({"message": "Baseline updated successfully", "baseline":allobjs.data}, status=status.HTTP_200_OK)
    
def reflect(id):
    all_objs = UniquePdfDataTable.objects.filter(viewuploaded=id)
    print(all_objs[0].bill_date)
    bill_date = all_objs[0].bill_date
    all_baseline = BaselineDataTable.objects.filter(viewuploaded=id)
    print(all_baseline)
    for base in all_baseline:
        base.bill_date = bill_date
        base.save()