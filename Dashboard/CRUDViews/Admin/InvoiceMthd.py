from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import InvoiceMethod
from ...Serializers.AdminPage import InvoiceMethodOperationSerializer, InvoiceMethodShowSerializer
from rest_framework.permissions import IsAuthenticated

from authenticate.views import saveuserlog


class InvoiceMethodView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk=None):
        if pk:
            invoice_method = InvoiceMethod.objects.get(name=pk)
            ser = InvoiceMethodShowSerializer(invoice_method)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        else:
            invoice_methods = InvoiceMethod.objects.all()
            ser = InvoiceMethodShowSerializer(invoice_methods, many=True)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        if InvoiceMethod.objects.filter(name=request.data["name"]).exists():
            return Response({"message": "Invoice method with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        ser = InvoiceMethodOperationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'New Invoice Method created: {ser.data["name"]}')
            return Response({"message" : "new Invoice method created successfully!", "data" : ser.data}, status=status.HTTP_201_CREATED)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk):
        try:
            invoice_method = InvoiceMethod.objects.get(name=pk)
        except InvoiceMethod.DoesNotExist:
            return Response({"message": 'Invoice Method not found'}, status=status.HTTP_404_NOT_FOUND)
        ser = InvoiceMethodOperationSerializer(invoice_method, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'Invoice Method updated: {ser.data["name"]}')
            return Response({"message" : "Invoice Method updated successfully!", "data" : ser.data}, status=status.HTTP_200_OK)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        try:
            invoice_method = InvoiceMethod.objects.get(name=pk)
            invoice_method.delete()
            saveuserlog(request.user, description=f'Invoice Method deleted: {pk}')
            return Response({'message':"Invoice Method Deleted Successfully!"}, status=status.HTTP_200_OK)    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
