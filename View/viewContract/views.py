from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from OnBoard.Organization.models import Organizations
from ..models import Contracts
from Dashboard.ModelsByPage.DashAdmin import Vendors
from .ser import showOrganizationSerializer, vendorshowSerializer, showContractSerializer, saveContractSerializer
from OnBoard.Ban.models import UploadBAN, BaseDataTable

class viewContractView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        orgs = showOrganizationSerializer(Organizations.objects.all(), many=True)
        vendors = vendorshowSerializer(Vendors.objects.all(), many=True)
        contracts = showContractSerializer(Contracts.objects.all(), many=True)

        return Response(
            {"orgs": orgs.data, "vendors": vendors.data, "contracts":contracts.data},
            status=status.HTTP_200_OK,
        )
    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            sub_company = data.pop('sub_company')[0]
            if not sub_company:
                return Response({"message":"Organization undefined!"}, status=status.HTTP_400_BAD_REQUEST)
            bannumber = data.pop('ban', None)
            ban = BaseDataTable.objects.filter(accountnumber=bannumber[0])
            if not ban.exists():
                return Response({"message": "BAN not found"}, status=status.HTTP_400_BAD_REQUEST)
            

            ban=ban[0]
            contract = Contracts.objects.filter(sub_company=sub_company, baseban=ban)
            if contract.exists():
                contract.delete()
            data = {
                'person' : f'{request.user.first_name} {request.user.last_name}',
                'baseban' :  ban,
                'sub_company': sub_company,
                'contract_name':data.pop('contract_name')[0],
                'contract_file': data.pop('contract_file')[0]
            }
            contract = Contracts.objects.create(**data)
            if contract:
                saveuserlog(
                    request.user,
                    f"Contract for ban {contract.baseban.accountnumber} uploaded successfully!"
                )
                return Response({"message": "Contract uploaded successfully"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": "Error in uploading contract!"},status=status.HTTP_400_BAD_REQUEST)

            
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, pk, *args, **kwargs):
        data = request.data
        try:
            obj = Contracts.objects.get(id=pk)
            data.pop('uploadedban', None)
            data.pop('baseban', None)
            data.pop('contract_file', None)
            data.pop('contract_name', None)
            ser = saveContractSerializer(obj, data=data, partial=True)
            if ser.is_valid():
                ser.save()
            else:
                return Response({"message": ser.errors}, status=status.HTTP_400_BAD_REQUEST)
            saveuserlog(request.user, f'Contract with name: {obj.contract_name} updated successfully!')  # TODO: log user action with ID and details.
            return Response({"message": "Contract updated successfully"}, status=status.HTTP_200_OK)
        except Contracts.DoesNotExist:
            return Response({"message": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, pk, *args, **kwargs):
        try:
            obj = Contracts.objects.get(id=pk)
            number = obj.uploadedban.account_number if obj.uploadedban else obj.baseban.accountnumber
            obj.delete()
            saveuserlog(request.user, f'Contract of ban {number} deleted successfully!')
            return Response({
                'message': f"Contract deleted successfully!"
            }, status=status.HTTP_200_OK)
        except Contracts.DoesNotExist:
            return Response({"message": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
