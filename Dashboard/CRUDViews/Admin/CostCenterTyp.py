from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import CostCenterType
from ...Serializers.AdminPage import CostCenterTypeOperationSerializer, CostCenterTypeShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog


class CostCenterTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            cost_center_type = CostCenterType.objects.get(name=pk)
            ser = CostCenterTypeShowSerializer(cost_center_type)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        else:
            cost_center_types = CostCenterType.objects.all()
            ser = CostCenterTypeShowSerializer(cost_center_types, many=True)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        ser = CostCenterTypeOperationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'New Cost Center Type created: {ser.data["name"]}') 
            return Response({"message" : "new cost center type created successfully!", "data":ser.data}, status=status.HTTP_201_CREATED) 
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk):
        try:
            cost_center_type = CostCenterType.objects.get(name=pk)
        except CostCenterType.DoesNotExist:
            return Response({"message": 'Cost Center Type not found'}, status=status.HTTP_404_NOT_FOUND)
        ser = CostCenterTypeOperationSerializer(cost_center_type, data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'Cost Center Type updated: {ser.data["name"]}')  
            return Response({"message" : "Cost Center Type updated successfully!", "data":ser.data}, status=status.HTTP_200_OK)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        try:
            cost_center_type = CostCenterType.objects.get(name=pk)
            cost_center_type.delete()
            saveuserlog(request.user, description=f'Cost Center Type deleted: {pk}")')
            return Response({'message':"Cost Center Type Deleted Successfully!"}, status=status.HTTP_200_OK)    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)