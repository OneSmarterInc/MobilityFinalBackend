
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..models import PortalInformation, BaseDataTable, UploadBAN
from .ser import showPortalInfoser
from OnBoard.Company.models import Company
from authenticate.views import saveuserlog
from Dashboard.ModelsByPage.DashAdmin import Vendors

class PortalInformationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk=None, *args, **kwargs):
        if pk:
            obj = PortalInformation.objects.get(id=pk)
            ser = showPortalInfoser(obj)
        else:
            all_objs = PortalInformation.objects.all()
            ser = showPortalInfoser(all_objs, many=True)

        return Response({"data" : ser.data,
        }, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        print("post")
        data = request.data.copy()
        print(data)
        acc = data.get("Account_number")
        ven = data.get("Vendor")
        com = data.get("company")
        obj = BaseDataTable.objects.filter(accountnumber=acc, vendor=ven, company=com)
        if not obj.exists():
            obj = UploadBAN.objects.filter(company=Company.objects.get(Company_name=com), Vendor=Vendors.objects.get(name=ven), account_number=acc)
            if not obj.exists():
                return Response({"message": f"{acc} not found!"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                data['banUploaded'] = obj[0].id
        else:
            data['banOnboarded'] = obj[0].banOnboarded.id
        try:
            ser = showPortalInfoser(data=data)
            if ser.is_valid():
                ser.save()
                return Response({"message" : "Portal Information Added successfully"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": str(ser.errors)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def put(self, request, pk, *args, **kwargs):
        pass
    def delete(self, request, pk, *args, **kwargs):
        pass
