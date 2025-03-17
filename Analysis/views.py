from django.shortcuts import render, HttpResponse

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Analysis
from .ser import AnalysisSaveSerializer, AnalysisShowSerializer, VendorsShowSerializer
from Dashboard.ModelsByPage.DashAdmin import Vendors

class AnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk is None:
            analysis = Analysis.objects.all()
            vendors = Vendors.objects.all()
            Vser = VendorsShowSerializer(vendors, many=True)
            ser = AnalysisShowSerializer(analysis, many=True)
            return Response({"data": ser.data, 'vendors':Vser.data}, status=status.HTTP_200_OK)
        else:
            try:
                analysis = Analysis.objects.get(id=pk)
                ser = AnalysisShowSerializer(analysis)
                return Response({"data": ser.data}, status=status.HTTP_200_OK)
            except Analysis.DoesNotExist:
                return Response({"message": "Analysis not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            ser = AnalysisSaveSerializer(data=request.data)
            if ser.is_valid():
                ser.save()
            else:
                print(ser.errors)
                return Response({"message": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
            try:
                id = ser.data['id']
                analy = ProcessAnanalysis(Analysis.objects.get(id=int(id)))
                
                ana = analy.process_pdf()
                if ana['Error'] != 0:
                    return Response({"message": ana['message']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    return Response({"message": "Analysis created successfully!", "data": ser.data}, status=status.HTTP_201_CREATED)
            except Exception as e:
                print(e)
                return Response({"message": f'Data saved but error processing file!{str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk):
        try:
            analysis = Analysis.objects.get(id=pk)
            ser = AnalysisSaveSerializer(analysis, data=request.data)
            if ser.is_valid():
                ser.save()
                return Response({"message": "Analysis updated successfully!", "data": ser.data}, status=status.HTTP_200_OK)
        except Analysis.DoesNotExist:
            return Response({"message": "Analysis not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        try:
            analysis = Analysis.objects.get(id=pk)
            analysis.delete()
            return Response({"message": "Analysis deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Analysis.DoesNotExist:
            return Response({"message": "Analysis not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
import json
class ProcessAnanalysis:
    def __init__(self, instance):
        self.instance = instance
        self.path = instance.uploadBill.path
        self.filename = instance.uploadBill.name
        self.company = instance.company.Company_name
        self.vendor = instance.vendor.name
        self.client = instance.client
        self.remark = instance.remark
        self.store = None
        self.user = instance.created_by
        print({"first_name": self.user.first_name, "last_name": self.user.last_name})
        self.acc_info = '1234567'
        self.types = None

    def process_pdf(self):
        print("def process_pdf")

        # AllUserLogs.objects.create(
        #         user_email=email,
        #         description=(
        #         f"User uploaded analysis file for {organization} with vendor {vendor_name}."
        #     )
        #     )
        buffer_data = json.dumps(
            {'pdf_path':self.path, 'vendor_name':self.vendor, 'pdf_filename':self.filename, 'user_id':self.user.id, 'organization':self.client, 'remark':self.remark, 'first_name':self.user.first_name, 'last_name':self.user.last_name, 'store':self.store, 'types':self.types}
        )
        print(buffer_data)
        from .Background.task import process_analysis_task
        try:
            process_analysis_task(self.instance, buffer_data)
            return {'message' : 'PDF processing completed successfully.', 'Error' : 0}
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return {'message' : f'Error processing PDF, {str(e)}', 'Error' : 1}

        
    
class download_analysis_xlsx_file(APIView):
    def get(self,request,pk):
        workbook = Analysis.objects.get(id=pk)
        excel_data = workbook.excel
        response = HttpResponse(excel_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={workbook.excel.name}'
        return response  