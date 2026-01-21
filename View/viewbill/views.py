from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from OnBoard.Organization.models import Organizations
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, BaselineDataTable, OnboardBan
from .ser import showOrganizationSerializer, showBanSerializer, vendorshowSerializer, basedatahowSerializer, paytypehowSerializer, uniquepdftableSerializer, BaselinedataSerializer, BaselineDataTableShowSerializer, showaccountbasetable, BaselineWithOnboardedCategorySerializer,showbaselinenotesSerializer, viewbillsSerializer, rawdataserializer
from Dashboard.ModelsByPage.DashAdmin import Vendors, PaymentType
from ..models import ViewUploadBill, PaperBill
from Batch.views import create_notification
class ViewBill(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        self.billMainObjs = None
        self.basedata = None
        self.uniquedata = None
        self.baseaccounts = None

    def get(self, request, org, *args, **kwargs):
        objs = Organizations.objects.filter(company=request.user.company)
        orgObj = request.user.organization
        orgObj = objs.filter(Organization_name=org).first() if not orgObj else orgObj
        if not orgObj:
            return Response({"message":"organizatio not found!"},status=status.HTTP_400_BAD_REQUEST)
        paytypes = paytypehowSerializer(PaymentType.objects.all(), many=True)
        uniquedata = uniquepdftableSerializer(UniquePdfDataTable.objects.filter(sub_company=org).filter(banOnboarded=None,banUploaded=None), many=True)
        baseaccounts = showaccountbasetable(BaseDataTable.objects.filter(sub_company=org).filter(viewuploaded=None, viewpapered=None), many=True)
        billMainObjs = viewbillsSerializer(ViewUploadBill.objects.filter(organization=orgObj), many=True)
        basedata = basedatahowSerializer(BaseDataTable.objects.filter(sub_company=org).filter(banOnboarded=None,banUploaded=None), many=True)

        raw_data = rawdataserializer(ViewUploadBill.objects.filter(organization=orgObj), many=True)

        return Response({
            "basedata" : basedata.data if basedata else None,
            "paytypes" : paytypes.data,
            "uniquedata" : uniquedata.data if uniquedata else None,
            "baseaccounts": baseaccounts.data if baseaccounts else None,
            "raw_data":raw_data.data,
            "uploaded_bills_objects": billMainObjs.data if billMainObjs else None
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
                request.user, f"Changed payment type to {request.data['paymentType']} for {obj.accountnumber}-{obj.bill_date}"
            )
        elif request.data['type'] == 'change-status':
            obj.billstatus = request.data['status']
            
            saveuserlog(
                request.user, f"Changed bill status to {request.data['status']} for {obj.accountnumber}-{obj.bill_date}"
            )
        elif request.data['type'] == 'change-check':
            obj.Check = request.data['check']
            
            saveuserlog(
                request.user, f"Changed check to {request.data['check']} for {obj.accountnumber}-{obj.bill_date}"
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
        # create_notification(request.user, f"Bill of account number {obj.accountnumber} and bill date {obj.bill_date} updated successfully!",request.user.company)
        
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
        # create_notification(request.user, f"Bill of account number {acc} and bill date {bd} deleted successfully!",request.user.company)
        return Response({"message": "Bill deleted successfully."}, status=status.HTTP_200_OK)

from datetime import datetime
class ViewBillBaseline(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        sub_company = request.GET.get('sub_company')
        print(sub_company)
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
            obj = BaselineDataTable.objects.filter(id=pk).first()
        except BaselineDataTable.DoesNotExist:
            return Response({"message": "Baseline Data not found"}, status=status.HTTP_404_NOT_FOUND)
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

from Dashboard.ModelsByPage.aimodels import BotChats
from Dashboard.Serializers.chatser import ChatSerializer
from bot import BotClass
import pandas as pd
class ViewBillBotView(APIView):
    permission_classes = [IsAuthenticated]
    connection = None
    schema = None

            
    def get(self,request,billType,pk,*args,**kwargs):
        if not pk:
            return Response({"message":"Key required!"},status=status.HTTP_400_BAD_REQUEST)
        
        chats = BotChats.objects.filter(billChat=pk)
        ser = ChatSerializer(chats, many=True)
        return Response({"data":ser.data},status=status.HTTP_200_OK)
        
    def post(self,request,billType,pk,*args,**kwargs):
        botObj = BotClass(bot_type="bill")
        data = request.data
        if not pk:
            return Response({"message":"Key required!"},status=status.HTTP_400_BAD_REQUEST)
        self.connection, self.schema = botObj.init_database()

        data = request.data
        question = data.get("prompt")
        baseId = data.get("base_id")
        chatHis=BotChats.objects.filter(M_analysisChat=pk).values("question", "response", "created_at")
        df = pd.DataFrame(list(chatHis))
        try:
            instance = BotChats.objects.create(
                user=request.user,
                question=question,
                billChat=BaseDataTable.objects.filter(id=baseId).first()
            )
            is_generated, sql_query = botObj.get_view_sql_from_gemini(question, self.schema, bill_type=billType, special_id=pk, chathistory=df)
            print("is generated==",is_generated, sql_query)
            if not is_generated:
                instance.is_query_generated = False
                instance.response = "I need a bit more info to answer.\nCould you please elaborate more on your question."
                instance.save()
                return Response({"response":"Unable to answer the question!"},status=status.HTTP_200_OK)
            is_ran, result_df = botObj.run_query(conn=self.connection, sql=sql_query)
            print(result_df)
            _is_check, response_text = botObj.make_human_response(question, result_df, db_schema=self.schema)
            print()
            allLines = response_text.split("\n")
            questions = [line.strip() for line in allLines if line.strip().endswith("?")]
            other_lines = "\n".join([line.strip() for line in allLines if line.strip() and not line.strip().endswith("?")])
            print(is_ran, result_df)
            instance.response = other_lines
            instance.recommended_questions = questions
            if is_ran:
                instance.is_query_generated = True
                instance.is_query_ran = True
            else:
                instance.is_df_empty = True
            instance.save()   
                

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
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)