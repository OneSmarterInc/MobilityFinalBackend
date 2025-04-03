from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from OnBoard.Organization.models import Organizations
from OnBoard.Ban.models import UploadBAN, BaseDataTable, UniquePdfDataTable, BaselineDataTable
from .ser import showOrganizationSerializer, showBanSerializer, vendorshowSerializer, basedatahowSerializer, paytypehowSerializer, uniquepdftableSerializer, baselinedataserializer
from Dashboard.ModelsByPage.DashAdmin import Vendors, PaymentType

class ViewBill(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        objs = Organizations.objects.all()
        ser = showOrganizationSerializer(objs, many=True)
        uniquedata = uniquepdftableSerializer(UniquePdfDataTable.objects.all(), many=True)
        bans = showBanSerializer(UploadBAN.objects.all(), many=True)
        vendors = vendorshowSerializer(Vendors.objects.all(), many=True)
        basedata = basedatahowSerializer(BaseDataTable.objects.all(), many=True)
        paytypes = paytypehowSerializer(PaymentType.objects.all(), many=True)
        return Response({
            "data" : ser.data,
            "bans" : bans.data,
            "vendors" : vendors.data,
            "basedata" : basedata.data,
            "paytypes" : paytypes.data,
            "uniquedata" : uniquedata.data,

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
            obj.paymentType = PaymentType.objects.get(name=request.data['paymentType'])
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
        obj.delete()
        saveuserlog(request.user, "Deleted Base Data with ID: " + str(pk))
        return Response({"message": "Base Data successfully deleted!"}, status=status.HTTP_200_OK)

class ViewBillBaseline(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        sub_company = request.GET.get('sub_company')
        vendor = request.GET.get('vendor')
        account_number = request.GET.get('account_number')

        objs = BaselineDataTable.objects.filter(vendor=vendor, account_number=account_number, sub_company=sub_company)
        ser = baselinedataserializer(objs, many=True)
        return Response({"data": ser.data}, status=status.HTTP_200_OK)