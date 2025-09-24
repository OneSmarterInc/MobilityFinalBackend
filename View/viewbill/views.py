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
        obj = BaseDataTable.objects.filter(id=pk).first()

        if not obj:
            return Response({"message": "Base Data not found"}, status=status.HTTP_404_NOT_FOUND)

        print(request.data)
        if request.data['type'] == 'change-payment':
            obj.paymentType = request.data['paymentType']
            saveuserlog(
                request.user, "Changed payment type to " + request.data['paymentType'] + " for: " + {obj.accountnumber}-{obj.bill_date}
            )
        elif request.data['type'] == 'change-status':
            obj.billstatus = request.data['status']
            saveuserlog(
                request.user, "Changed bill status to " + request.data['status'] + " for: " + {obj.accountnumber}-{obj.bill_date}
            )
        elif request.data['type'] == 'change-check':
            obj.Check = request.data['check']
            saveuserlog(
                request.user, "Changed check to " + request.data['check'] + " for: " + {obj.accountnumber}-{obj.bill_date}
            )
        elif request.data['type'] == 'add-summaryfile':
            obj.summary_file = request.data['file']
   
            saveuserlog(
                request.user, f"Added summary file for {obj.accountnumber}-{obj.bill_date}"
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
        obj = BaseDataTable.objects.filter(id=pk).first()
        if not obj:
            return Response({"message": "Base Data not found"}, status=status.HTTP_404_NOT_FOUND)
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
        saveuserlog(request.user, f"Bill of account number {acc} and bill date {bd} deleted successfully!")
        return Response({"message": "Bill deleted successfully."}, status=status.HTTP_200_OK)

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
            saveuserlog(
            request.user,
                f"Baseline with account number {obj.account_number} and wireless number {obj.Wireless_number} moved to draft"
            )
        elif action == "is_pending":
            obj.is_draft = False
            obj.is_pending = True
            saveuserlog(
            request.user,
                f"Baseline with account number {obj.account_number} and wireless number {obj.Wireless_number} moved to pending"
            )
        else:
            return Response({"message": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        obj.save()
        saveuserlog(
            request.user,
            f"Baseline with account number {obj.account_number} and wireless number {obj.Wireless_number} updated"
        )
        return Response({"message": "Baseline updated successfully"}, status=status.HTTP_200_OK)
    
def reflect(id):
    all_objs = UniquePdfDataTable.objects.filter(viewuploaded=id)
    print(all_objs[0].bill_date)
    bill_date = all_objs[0].bill_date
    all_baseline = BaselineDataTable.objects.filter(viewuploaded=id)
    print(all_baseline)
    for base in all_baseline:
        base.bill_date = bill_date
        base.save()
# from ..bot import get_database, get_response_from_gemini, get_sql_from_gemini, execute_sql_query
from ..bot import init_database, get_sql_from_gemini, run_query, make_human_response

from Dashboard.ModelsByPage.aimodels import BotChats
from Dashboard.Serializers.chatser import ChatSerializer

class ViewBillBotView(APIView):
    permission_classes = [IsAuthenticated]
    connection = None
    schema = None

    @classmethod
    def initialize_db(cls, billType, billID):
        """Initialize DB connection + schema once."""
        if cls.connection is None or cls.schema is None:
            cls.connection, cls.schema = init_database("db.sqlite3",billType=billType, billId=billID)
            
    def get(self,request,billType,pk,*args,**kwargs):
        if not pk:
            return Response({"message":"Key required!"},status=status.HTTP_400_BAD_REQUEST)
        
        chats = BotChats.objects.filter(billChat=pk)
        ser = ChatSerializer(chats, many=True)
        return Response({"data":ser.data},status=status.HTTP_200_OK)
        
    def post(self,request,billType,pk,*args,**kwargs):
        data = request.data
        if not pk:
            return Response({"message":"Key required!"},status=status.HTTP_400_BAD_REQUEST)
        self.initialize_db(billType=billType, billID=pk)

        data = request.data
        question = data.get("prompt")
        baseId = data.get("base_id")
        try:
            sql_query = get_sql_from_gemini(question, self.schema)


            result_df = run_query(conn=self.connection, sql=sql_query, billType=billType, billId=pk)

            if result_df is None:
                return Response(
                    {"message": "No data found for the given query."},
                    status=status.HTTP_200_OK
                )
            

            response_text = make_human_response(question, result_df)
            print(response_text)
            BotChats.objects.create(
                    user=request.user,
                    question=question,
                    response=response_text,
                    billChat=BaseDataTable.objects.filter(id=baseId).first()
            )
                

            # saveuserlog(request.user, f"Chatbot query executed: {question} | Response: {response_text}")

            return Response(
                {"response": response_text},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"Error processing request: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    def delete(self,request,pk,*args,**kwargs):
        try:
            chats = BotChats.objects.filter(billChat=pk)
            chats.delete()
            return Response({"message":"user chat deleted!"},status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message":"Internal Server Error!"},status=status.HTTP_400_BAD_REQUEST)