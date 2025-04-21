from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from  .models import Company
from .ser import CompanyOperationSerializer, CompanyShowSerializer
from rest_framework.permissions import IsAuthenticated
from Dashboard.ModelsByPage.DashAdmin import Vendors
from Dashboard.Serializers.AdminPage import VendorsShowSerializer

from authenticate.views import saveuserlog

class CompanyView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk=None):
        if pk:
            company = Company.objects.get(Company_name=pk)
            serializer = CompanyShowSerializer(company)
            return Response({"data" : serializer.data}, status=status.HTTP_200_OK)
        else:
            companies = Company.objects.all()
            vendors = VendorsShowSerializer(Vendors.objects.all(), many=True)
            serializer = CompanyShowSerializer(companies, many=True)
            return Response({"data" : serializer.data, "vendors" : vendors.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        print(request.data)
        if Company.objects.filter(Company_name=request.data["Company_name"]).exists():
            return Response({"message": "Company with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CompanyOperationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, f"company named {serializer.data['Company_name']} created successfully!")
            return Response({"message" : "Comapany created successfully!", "data" : serializer.data}, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        company = Company.objects.get(Company_name=pk)
        serializer = CompanyOperationSerializer(company, data=request.data)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, f"company named {pk} updated successfully!") 
            return Response({"message" : "Company updated successfully!", "data" : serializer.data}, status=status.HTTP_200_OK)
        return Response({"message" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            company = Company.objects.get(Company_name=pk)
        except Company.DoesNotExist:
            return Response({"message" : "Company not found!"}, status=status.HTTP_404_NOT_FOUND)
        
        company.delete()
        saveuserlog(request.user, f"company named {pk} deleted successfully!")
        return Response({"message" : "Company deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
