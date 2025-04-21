from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from .models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors
from ..Company.models import Company
from Dashboard.Serializers.AdminPage import VendorsShowSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from .ser import OrganizationSaveSerializer, OrganizationShowSerializer, DivisionSerializer, LinkSerializer, DivisionNameSerializer
from authenticate.views import saveuserlog

class OnboardOrganizationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        company = Company.objects.get(Company_name=request.data["company"])
        data = request.data.copy()
        st = type(data.get('status'))
        if st == 'false':
            data['status'] = 0
        else:
            data['status'] = 1
        
        if Organizations.objects.filter(Organization_name=data["Organization_name"], company=company).exists():
            print("already exists")
            return Response({"message": "Location with this site_name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = OrganizationSaveSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            orgobj = Organizations.objects.get(Organization_name=serializer.data['Organization_name'])
            saveuserlog(request.user, f'Organization with name {serializer.data["Organization_name"]} created successfully!')
            return Response({"message" : "Organization created successfully!", "data" : serializer.data}, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, pk=None):
        if pk is None:
            organizations = Organizations.objects.all()
            serializer = OrganizationShowSerializer(organizations, many=True)
            vendors = VendorsShowSerializer(Vendors.objects.all(), many=True)
            
            return Response({
                "data": serializer.data, 
                "vendors": vendors.data,
            }, status=status.HTTP_200_OK)
        else:
            try:
                organization = Organizations.objects.get(Organization_name=pk)
                serializer = OrganizationShowSerializer(organization)
                divisions = DivisionNameSerializer(Division.objects.filter(organization=organization), many=True)
                return Response({"data": serializer.data, "divisions": divisions.data}, status=status.HTTP_200_OK)
            except Organizations.DoesNotExist:
                return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
            
    def put(self, request, pk):
        try:
            organization = Organizations.objects.get(id=pk)
        except Organizations.DoesNotExist:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrganizationSaveSerializer(organization, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, f'Organization with name {pk} updated successfully!')  
            return Response({"message" : "Organization updated successfully!", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            organization = Organizations.objects.get(Organization_name=pk)
            organization.delete()
            saveuserlog(request.user, f'Organization with name {pk} deleted successfully!')
            return Response({"message": "Organization deleted successfully!"}, status=status.HTTP_200_OK)
        except Organizations.DoesNotExist:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        

from .models import Division


class DivisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, org):
        try:
            organization = Organizations.objects.get(id=org)
            org_name = organization.Organization_name
            company_name = organization.company.Company_name
        except Organizations.DoesNotExist:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = DivisionSerializer(data={"organization": org_name, 'company' : company_name, **request.data})
        try:
            if serializer.is_valid():
                serializer.save()
                saveuserlog(request.user, f'Division with name {serializer.data["name"]} created successfully!')
                return Response({"message" : "Division created successfully!", "data" : serializer.data}, status=status.HTTP_201_CREATED)
            else:
                print(serializer.errors)
                return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)        
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get(self, request, org, pk=None):
        if pk is None:
            divisions = Division.objects.filter(organization=org)
            serializer = DivisionSerializer(divisions, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        else:
            try:
                division = Division.objects.filter(organization=org, name=pk).first()
                serializer = DivisionSerializer(division)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            except Division.DoesNotExist:
                return Response({"message": "Division not found"}, status=status.HTTP_404_NOT_FOUND)
        
    def put(self, request, org, pk):
        try:
            organization = Organizations.objects.get(id=org)
            org_name = organization.Organization_name
            company_name = organization.company.Company_name
        except Organizations.DoesNotExist:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            division = Division.objects.get(organization=org, id=pk)
        except Division.DoesNotExist:
            return Response({"message": "Division not found"}, status=status.HTTP_404_NOT_FOUND)
        try:

            serializer = DivisionSerializer(division, data={"organization": org_name, 'company' : company_name, **request.data})
            if serializer.is_valid():
                serializer.save()
                saveuserlog(request.user, f'Division with name {division.name} updated successfully!')
                return Response({"message" : "Division updated successfully!", "data": serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, org, pk):
        try:
            division = Division.objects.filter(organization=org, id=pk).first()
        except Division.DoesNotExist:
            return Response({"message": "Division not found"}, status=status.HTTP_404_NOT_FOUND)
        division.delete()
        saveuserlog(request.user, f'Division with name {pk} deleted successfully!')
        return Response({"message": "Division deleted successfully!"}, status=status.HTTP_200_OK)
        
from .models import Links

class LinksView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, org):
        try:
            organization = Organizations.objects.get(id=org)
            org_name = organization.Organization_name
            company_name = organization.company.Company_name
        except Organizations.DoesNotExist:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            for data in request.data:
                serializer = LinkSerializer(data={"organization": org_name, 'company' : company_name, **data})
                if serializer.is_valid():
                    serializer.save()
                    saveuserlog(request.user, f'Link with name {serializer.data["name"]} created successfully!')
                else:
                    return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message" : "Link created successfully!", "data" : serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def get(self, request, org, pk=None):
        if pk is None:
            links = Links.objects.filter(organization=org)
            serializer = LinkSerializer(links, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        else:
            try:
                link = Links.objects.get(name=pk)
                serializer = LinkSerializer(link)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            except Links.DoesNotExist:
                return Response({"message": "Link not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, org, pk):
        try:
            organization = Organizations.objects.get(id=org)
            org_name = organization.Organization_name
            company_name = organization.company.Company_name
        except Organizations.DoesNotExist:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            link = Links.objects.filter(organization=org, name=pk).first()
        except Links.DoesNotExist:
            return Response({"message": "Link not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = LinkSerializer(link, data={"organization": org_name, 'company' : company_name, **request.data})
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, f'Link with name {pk} updated successfully!')
            return Response({"message" : "Link updated successfully!", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, org, pk):
        try:
            link = Links.objects.filter(organization=org, name=pk).first()
            link.delete()
            saveuserlog(request.user, f'Link with name {pk} deleted successfully!')
            return Response({"message": "Link deleted successfully!"}, status=status.HTTP_200_OK)
        except Links.DoesNotExist:
            return Response({"message": "Link not found"}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def ChangeOrgStatus(request, pk):
    try:
        organization = Organizations.objects.get(id=pk)
    except Organizations.DoesNotExist:
        return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
    try:
        stat = int(request.data.get('status'))
        if stat == 0:
            organization.status = 0
            string_status = 'Inactive'
        elif stat == 1:
            organization.status = 1
            string_status = 'Active'
        elif stat == -1:
            organization.status = -1
            string_status = 'Closed'
        else:
            return Response({"message": "Invalid status. Status should be Active, Inactive, or Closed."}, status=status.HTTP_400_BAD_REQUEST)
        organization.save()
        saveuserlog(request.user, f'Organization status changed to {string_status} for {organization.Organization_name}')
        return Response({"message": f"Organization status changed to {string_status}."}, status=status.HTTP_200_OK)
    except Exception as e:
        print("error", e)
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)