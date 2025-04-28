
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

    def get(self, request,pk=None,*args, **kwargs):
        
        obj = PortalInformation.objects.filter(id=pk)
        if not obj.exists():
            return Response({"message":f"Portal Information not found!"},status=status.HTTP_400_BAD_REQUEST)
        obj = obj[0]
        
        ser = showPortalInfoser(obj)
        print(ser.data)

        return Response({"data" : ser.data,
        }, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        pass
    def put(self, request, pk, *args, **kwargs):
        
        print("put")
        data = request.data.copy()
        try:
            obj = PortalInformation.objects.get(id=pk)
        except PortalInformation.DoesNotExist:
            return Response({"message":f"Portal Information not found!"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message":f"{str(e)}"},status=status.HTTP_400_BAD_REQUEST)
        print(data)
    
        try:
            ser = showPortalInfoser(obj, data=data,partial=True)
            if ser.is_valid():
                ser.save()
                return Response({"message" : "Portal Information Added successfully"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"message": str(ser.errors)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def delete(self, request, pk, *args, **kwargs):
        pass
