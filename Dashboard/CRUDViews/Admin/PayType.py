from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import PaymentType
from ...Serializers.AdminPage import PaymentTypeOperationSerializer, PaymentTypeShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog

class PaymentTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            payment_type = PaymentType.objects.get(name=pk)
            ser = PaymentTypeShowSerializer(payment_type)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        else:
            payment_types = PaymentType.objects.all()
            ser = PaymentTypeShowSerializer(payment_types, many=True)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        if PaymentType.objects.filter(name=request.data["name"]).exists():
            return Response({"message": " Payment type with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        ser = PaymentTypeOperationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, "Added new payment type")
            return Response({"message" : "new payment type created successfully!", "data":ser.data}, status=status.HTTP_201_CREATED)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk):
        try:
            payment_type = PaymentType.objects.get(name=pk)
        except PaymentType.DoesNotExist:
            return Response({"message": 'Payment Type not found'}, status=status.HTTP_404_NOT_FOUND)
        ser = PaymentTypeOperationSerializer(payment_type, data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'Payment Type updated: {ser.data["name"]}') 
            return Response({"message" : "payment type updated successfully!", "data":ser.data}, status=status.HTTP_200_OK)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        try:
            payment_type = PaymentType.objects.get(name=pk)
            payment_type.delete()
            saveuserlog(request.user, description=f'Payment Type deleted: {pk}')
            return Response({'message':"Payment Type Deleted Successfully!"}, status=status.HTTP_200_OK)    
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)