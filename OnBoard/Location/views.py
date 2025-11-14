from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from  .models import Location, BulkLocation
from ..Organization.models import Organizations, Division
from ..Company.models import Company
from .ser import LocationSaveSerializer, LocationShowSerializer, LocationSerializer, showDivisions, showOrgs
import pandas as pd
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog
class LocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, org=None, pk=None):
        if pk:
            location = Location.objects.get(organization=org, site_name=pk)
            serializer = LocationShowSerializer(location)
        else:
            locations = Location.objects.filter(organization=org)
            serializer = LocationShowSerializer(locations, many=True)
        divisions = showDivisions(Division.objects.all(), many=True)
        orgs = showOrgs(Organizations.objects.filter(company=request.user.company), many=True)
        print(divisions.data, orgs.data)
        return Response({"data" : serializer.data, "organizations":orgs.data, "divisions":divisions.data}, status=status.HTTP_200_OK)
        
    def post(self, request, org=None, *args, **kwargs):
        print(request.data)
        if org==None:
            data = request.data
            org = data['organization']
            organization = Organizations.objects.filter(Organization_name=org)
            if not organization.exists():
                return Response({"message": f"Organization with name {org} not found"}, status=status.HTTP_404_NOT_FOUND)
            organization = organization[0]
        else:
            try:
                organization = Organizations.objects.get(id=org)
                company_name = organization.company.Company_name
            except Organizations.DoesNotExist:
                return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        try:
            print("organ=", organization)
            if 'division' in request.data and request.data['division']:
                print(request.data['division'])
                division = Division.objects.get(name=request.data['division'], organization=organization)
            else:
                division = None
            if Location.objects.filter(organization=organization, site_name=request.data["site_name"]).exists():
                print("already exists")
                return Response({"message": "Location with this site_name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
            print("div=",division)
            data = request.data.copy()
            data.pop('division', None)
            data.pop('organization', None)
            data = {"organization": organization, 'company' : organization.company, 'division': division, **data}
            cleaned_data = {key: value[0] if isinstance(value, list) else value for key, value in data.items()}
            print(cleaned_data)
            loc = Location.objects.create(
                **cleaned_data,
            )
            loc.save()
            saveuserlog(request.user, f"new location with site name {data['site_name']} for organization f{organization.Organization_name} created successfully!")
            return Response({"message": "Location created successfully!", "data": loc.site_name}, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            return Response({"message": "Unable to create location."}, status=status.HTTP_400_BAD_REQUEST)

        
    def put(self, request, org, pk, *args, **kwargs):
        print(pk)
        if isinstance(org, str):
            org = Organizations.objects.filter(Organization_name=org).first()
        else:
            org = Organizations.objects.get(id=org)

        try:
            location = Location.objects.get(id=pk)
        except Location.DoesNotExist:
            return Response({"message": "Location not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            request_data = request.data.copy()
            division_name = request_data.pop('division', None)
            division = Division.objects.filter(name=division_name, organization=location.organization)

            # --- Capture Original Data ---
            original_data = {
                field.name: getattr(location, field.name)
                for field in location._meta.fields
                if field.name in request_data or field.name == "division"
            }

            # --- Update Fields ---
            for key, value in request_data.items():
                setattr(location, key, value[0] if isinstance(value, list) else value)

            if division.exists():
                location.division = division[0]

            location.save()

            # --- Capture Updated Data ---
            updated_data = {
                field: getattr(location, field)
                for field in original_data
            }

            # --- Prepare Change Log ---
            change_log_lines = []
            for field, old_val in original_data.items():
                new_val = updated_data.get(field)
                if old_val != new_val:
                    change_log_lines.append(f"{field}: '{old_val}' → '{new_val}'")

            change_log = "; ".join(change_log_lines) if change_log_lines else "No changes detected."

            # --- Save Log Entry ---
            saveuserlog(
                request.user,
                f"Location of organization {org.Organization_name} name '{location.site_name}' updated. Changes: {change_log}"
            )

            return Response({"message": "Location updated successfully!"}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({"message": "Unable to update location."}, status=status.HTTP_400_BAD_REQUEST)


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
            loc = Location.objects.get(id=pk)
        except Location.DoesNotExist:
            return Response({"message" : "Location not found!"}, status=status.HTTP_404_NOT_FOUND)
        name = loc.site_name
        loc.delete()
        saveuserlog(request.user, f"location with site name {name} deleted successfully!") 
        return Response({"message" : "Location deleted successfully!"}, status=status.HTTP_200_OK)

from addon import parse_until_dict

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
            data = request.data
            print(data)
            division = data.get('division')
            div_obj = Division.objects.filter(name=division).first()
            mapping = parse_until_dict(data.get('mapping'))
            mapping_inverted = {v: k for k, v in mapping.items()}

            # Keep only mapped columns
            df = df[[col for col in mapping_inverted if col in df.columns]]

            # Rename columns using the inverted mapping
            df = df.rename(columns=mapping_inverted)

            print(df,df.columns)
            to_db = add_bulk_file(organization, file)
            if not to_db:
                return Response({'message': 'Failed to add bulk locations.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)                
            columns = df.columns.to_list()
            for index, row in df.iterrows():
                data = {column: value for column, value in zip(columns, row)}
                print(data)
                obj = Location.objects.create(bulkfile=to_db, company=organization.company, organization=organization, division=div_obj, **data)
                obj.save()
            saveuserlog(request.user, f"bulk locations uploaded successfully for organization {organization.Organization_name}")
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
    