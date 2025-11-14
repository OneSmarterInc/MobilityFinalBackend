from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import ManuallyAddedCompany
from ...Serializers.AdminPage import CompanyOperationSerializer, CompanyShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog



class CompanyView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk=None):
        if pk:
            company = ManuallyAddedCompany.objects.get(name=pk)
            serializer = CompanyShowSerializer(company)
            return Response({"data" : serializer.data}, status=status.HTTP_200_OK)
        else:
            companies = ManuallyAddedCompany.objects.all()
            serializer = CompanyShowSerializer(companies, many=True)
            return Response({"data" : serializer.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        if ManuallyAddedCompany.objects.filter(name=request.data["name"]).exists():
            return Response({"message": "company with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CompanyOperationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, description=f'New Company created: {serializer.data["name"]}')
            return Response({"message" : "Comapany created successfully!", "data" : serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"message" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        company = ManuallyAddedCompany.objects.get(name=pk)
        serializer = CompanyOperationSerializer(company, data=request.data)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, description=f'Company updated: {serializer.data["name"]}')
            return Response({"message" : "Company updated successfully!", "data" : serializer.data}, status=status.HTTP_200_OK)
        return Response({"message" : serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            company = ManuallyAddedCompany.objects.get(name=pk)
        except ManuallyAddedCompany.DoesNotExist:
            return Response({"message" : "Company not found!"}, status=status.HTTP_404_NOT_FOUND)
        
        company.delete()
        saveuserlog(request.user, description=f'Company deleted: {pk}')
        return Response({"message" : "Company deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
