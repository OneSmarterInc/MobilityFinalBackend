from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from OnBoard.Organization.models import Organizations, Contract
from Dashboard.ModelsByPage.DashAdmin import Vendors
from .ser import showOrganizationSerializer, vendorshowSerializer, showContractSerializer

class viewContractView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        orgs = showOrganizationSerializer(Organizations.objects.all(), many=True)
        vendors = vendorshowSerializer(Vendors.objects.all(), many=True)
        contracts = showContractSerializer(Contract.objects.all(), many=True)

        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "contracts":contracts.data},
            status=status.HTTP_200_OK,
        )
    def post(self, request, *args, **kwargs):
        pass
    def put(self, request, pk, *args, **kwargs):
        data = request.data
        try:
            obj = Contract.objects.get(id=pk)
            obj.created_by = data['created_by'] if data['created_by'] is not None else obj.created_by
            obj.term = data['term'] if data['term'] is not None else obj.term
            obj.status = data['status'] if data['status'] is not None else obj.status
            obj.notes = data['notes'] if data['notes'] is not None else obj.notes
            obj.created = data['created'] if data['created'] is not None else obj.created
            obj.save()
            saveuserlog(request.user, f'Contract between organization {obj.organization.Organization_name} and vendor {obj.vendor.name} updated successfully!')
            return Response({
                'message': f"Contract updated successfully!"
            }, status=status.HTTP_200_OK)
        except Contract.DoesNotExist:
            return Response({"message": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request, pk, *args, **kwargs):
        try:
            obj = Contract.objects.get(id=pk)
            org = obj.organization.Organization_name
            ven = obj.vendor.name
            obj.delete()
            saveuserlog(request.user, f'Contract between organization {org} and vendor {ven} deleted successfully!')
            return Response({
                'message': f"Contract deleted successfully!"
            }, status=status.HTTP_200_OK)
        except Contract.DoesNotExist:
            return Response({"message": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
