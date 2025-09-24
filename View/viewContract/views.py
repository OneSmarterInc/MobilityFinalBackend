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
from OnBoard.Ban.models import UploadBAN, BaseDataTable, OnboardBan

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
                return Response({"message": "Organization undefined!"}, status=status.HTTP_400_BAD_REQUEST)

            org = Organizations.objects.filter(Organization_name=sub_company).first()
            if not org:
                return Response({"message": "Organization not found!"}, status=status.HTTP_400_BAD_REQUEST)

            bannumber = data.pop('ban', None)
            uploadedban = UploadBAN.objects.filter(organization=org, account_number=bannumber[0]).first()
            onboardedban = OnboardBan.objects.filter(organization=org, account_number=bannumber[0]).first()

            # if uploadedban:
            #     uploadedban.contract_file = data.pop('contract_file')[0]
            #     uploadedban.save()
            # if onboardedban:
            #     onboardedban.contract_file = data.pop('contract_file')[0]
            #     onboardedban.save()

            data = {
                'person': f'{request.user.first_name} {request.user.last_name}',
                'uploadedban': uploadedban,
                'onboardedban': onboardedban,
                'sub_company': sub_company,
                'contract_name': data.pop('contract_name')[0],
                'contract_file': data.pop('contract_file')[0]
            }

            contractObj = Contracts.objects.filter(uploadedban=uploadedban, onboardedban=onboardedban).first()

            if contractObj:
                for k, v in data.items():
                    setattr(contractObj, k, v)
                contractObj.save()

                accountNo = contractObj.uploadedban.account_number if contractObj.uploadedban else contractObj.onboardedban.account_number
                saveuserlog(request.user, f"Contract for ban {accountNo} updated successfully!")
                return Response({"message": "Contract updated successfully"}, status=status.HTTP_201_CREATED)

            else:
                contractObj = Contracts.objects.create(**data)
                accountNo = contractObj.uploadedban.account_number if contractObj.uploadedban else contractObj.onboardedban.account_number
                saveuserlog(request.user, f"Contract for ban {accountNo} created successfully!")
                return Response({"message": "Contract uploaded successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(e)
            return Response({"message": "Internal Server Error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk, *args, **kwargs):
        data = request.data
        try:
            obj = Contracts.objects.filter(id=pk)
            valid_fields = set(f.name for f in Contracts._meta.get_fields())
            update_data = {k: v for k, v in data.items() if k in valid_fields}
            obj.update(**update_data)
            saveuserlog(request.user, f'Contract with name: {obj.first().contract_name} updated successfully!')  # TODO: log user action with ID and details.
            return Response({"message": "Contract updated successfully"}, status=status.HTTP_200_OK)
            
        except Contracts.DoesNotExist:
            return Response({"message": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({"message": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, pk, *args, **kwargs):
        try:
            obj = Contracts.objects.get(id=pk)
            number = obj.uploadedban.account_number if obj.uploadedban else obj.onboardedban.account_number
            obj.delete()
            saveuserlog(request.user, f'Contract of ban {number} deleted successfully!')
            return Response({
                'message': f"Contract deleted successfully!"
            }, status=status.HTTP_200_OK)
        except Contracts.DoesNotExist:
            return Response({"message": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({"message": "Unable to delete Contract"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
