from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from  .models import Location, BulkLocation
from ..Organization.models import Organizations, Division
from ..Company.models import Company
from .ser import LocationSaveSerializer, LocationShowSerializer, LocationSerializer
import pandas as pd
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog
class LocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, org, pk=None):
        if pk:
            location = Location.objects.get(organization=org, site_name=pk)
            serializer = LocationShowSerializer(location)
            return Response({"data" : serializer.data}, status=status.HTTP_200_OK)
        else:
            locations = Location.objects.filter(organization=org)
            serializer = LocationShowSerializer(locations, many=True)
            return Response({"data" : serializer.data}, status=status.HTTP_200_OK)
        
    def post(self, request, org, *args, **kwargs):
        try:
            organization = Organizations.objects.pop(id=org)
            company_name = organization.company.Company_name
        except Organizations.DoesNotExist:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            division = Division.objects.get(name=request.data.pop('division'), organization=organization)
            
            data = {"organization": organization, 'company' : Company.objects.get(Company_name=company_name), 'division': division, **request.data}
            cleaned_data = {key: value[0] if isinstance(value, list) else value for key, value in data.items()}
            loc = Location.objects.create(
                **cleaned_data,
            )
            loc.save()
            saveuserlog(request.user, f"new location with site name {data['site_name']} created successfully!")
            return Response({"message": "Location created successfully!", "data": loc.site_name}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
    def put(self, request, org, pk, *args, **kwargs):
        if type(org) is str:
            org = Organizations.objects.filter(Organization_name=org).first()
        else:
            org = Organizations.objects.get(id=org)
        try:
            location = Location.objects.get(organization=org, id=pk)
        except Location.DoesNotExist:
            return Response({"message": "Location not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            
            request_data = request.data.copy()
            
            division_name = request_data.pop('division')  # Now it's mutable, no error
            division = Division.objects.filter(name=division_name, organization=location.organization)
            
            data = {'division': division[0] if division else None, **request_data}
            cleaned_data = {key: value[0] if isinstance(value, list) else value for key, value in data.items()}
            
            # Update fields
            for key, value in request_data.items():
                setattr(location, key, value[0] if isinstance(value, list) else value)
            
            if division:
                location.division = division  
            
            location.save()  
            saveuserlog(request.user, f"location with site name {pk} updated successfully!")
            
            return Response({"message": "Location updated successfully!"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # serializer = LocationSaveSerializer(location, data=request.data)
        # if serializer.is_valid():
        #     serializer.save()
        #     saveuserlog(request.user, f"location with site name {pk} updated successfully!")
        #     return Response({"message": "Location updated successfully!", "data": serializer.data}, status=status.HTTP_200_OK)
        # else:
        #     return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, org, pk):
        if type(org) is str:
            org = Organizations.objects.filter(Organization_name=org).first()
        else:
            org = Organizations.objects.get(id=org)
        try:
            loc = Location.objects.get(organization=org, id=pk)
        except Location.DoesNotExist:
            return Response({"message" : "Location not found!"}, status=status.HTTP_404_NOT_FOUND)
        loc.delete()
        saveuserlog(request.user, f"location with site name {pk} deleted successfully!") 
        return Response({"message" : "Location deleted successfully!"}, status=status.HTTP_200_OK)
        

class LocationBulkUpload(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, org):
        try:
            organization = Organizations.objects.get(id=org)
        except Organizations.DoesNotExist:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            file = request.data['file']
            print(file)
            if file.name.endswith('csv'):
                df = pd.read_csv(file)
            elif file.name.endswith('xlsx') or file.name.endswith('xls'):
                df = pd.read_excel(file)
            else:
                return Response({'message': 'Invalid file format. Only CSV and Excel files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)
            print(df)
            to_db = add_bulk_file(organization, file)
            if not to_db:
                return Response({'message': 'Failed to add bulk locations.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                saveuserlog(request.user, f"bulk locations uploaded successfully for organization {organization.Organization_name}")
            
            columns = df.columns.to_list()
            for index, row in df.iterrows():
                data = {column: value for column, value in zip(columns, row)}
                if 'division' in data and data['division'] is not None:
                    div = Division.objects.filter(name=data.pop('division'))
                    if div.exists():
                        div = div.first()
                    else:
                        div = None
                else:
                    div=None
                    data.pop('division')
                print(data)
                obj = Location.objects.create(bulkfile=to_db, company=organization.company, organization=organization, division=div, **data)
                obj.save()
            return Response({'message': 'Bulk locations added successfully!'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error in bulk upload: {e}")
            return Response({'message': f'Failed to upload bulk locations. due to {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def add_bulk_file(org, file):
    try:
        obj = BulkLocation.objects.create(organization=org, file=file)
        obj.save()
        return obj
    except Exception as e:
        print(f"Error adding bulk file: {e}")
        return False
    