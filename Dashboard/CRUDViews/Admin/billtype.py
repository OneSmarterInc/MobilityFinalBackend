from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import BillType
from authenticate.views import saveuserlog
from ...Serializers.AdminPage import saveBilltypeSerializer, BilltypeShowSerializer
from rest_framework.permissions import IsAuthenticated


class BillTypeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk=None):
        if pk:
            bill_type = BillType.objects.get(name=pk)
            ser = BilltypeShowSerializer(bill_type)
            return Response({"data": ser.data}, status=status.HTTP_200_OK)
        else:
            bill_types = BillType.objects.all()
            ser = BilltypeShowSerializer(bill_types, many=True)
            return Response({"data": ser.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        if BillType.objects.filter(name=request.data["name"]).exists():
            return Response({"message": "Bill type with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = saveBilltypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, description=f'New Bill Type created: {serializer.data["name"]}')
            return Response({"message": "New Bill Type created successfully!", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        if pk:
            bill_type = BillType.objects.get(name=pk)
            serializer = saveBilltypeSerializer(bill_type, data=request.data)
            if serializer.is_valid():
                serializer.save()
                saveuserlog(request.user, description=f'Bill Type updated: {serializer.data["name"]}')
                return Response({"message": "Bill Type updated successfully!", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Bill Type not found"}, status=status.HTTP_404_NOT_FOUND)
        
    def delete(self, request, pk):
        if pk:
            bill_type = BillType.objects.get(name=pk)
            bill_type.delete()
            saveuserlog(request.user, description=f'Bill Type deleted: {pk}')
            return Response({"message": "Bill Type deleted successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Bill Type not found"}, status=status.HTTP_404_NOT_FOUND)