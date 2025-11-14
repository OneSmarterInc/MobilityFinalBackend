from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import CostCenterLevel
from ...Serializers.AdminPage import CostCenterLevelOperationSerializer, CostCenterLevelShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog


class CostCenterLevelView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            cost_center_level = CostCenterLevel.objects.get(name=pk)
            ser = CostCenterLevelShowSerializer(cost_center_level)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        else:
            cost_center_levels = CostCenterLevel.objects.all()
            ser = CostCenterLevelShowSerializer(cost_center_levels, many=True)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        if CostCenterLevel.objects.filter(name=request.data["name"]).exists():
            return Response({"message": "Cost center level with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        ser = CostCenterLevelOperationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'New Cost Center Level created: {ser.data["name"]}')  # save user log in the database
            return Response({"message" : "cost center level created successfully!", "data" : ser.data}, status=status.HTTP_201_CREATED)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk):
        try:
            cost_center_level = CostCenterLevel.objects.get(name=pk)
        except CostCenterLevel.DoesNotExist:
            return Response({"message": 'Cost Center Level not found'}, status=status.HTTP_404_NOT_FOUND)
        ser = CostCenterLevelOperationSerializer(cost_center_level, data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'Cost Center Level updated: {ser.data["name"]}')
            return Response({"message" : "cost center updated successfully!", "data" : ser.data}, status=status.HTTP_200_OK)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        try:
            cost_center_level = CostCenterLevel.objects.get(name=pk)
            cost_center_level.delete()
            saveuserlog(request.user, description=f'Cost Center Level deleted: {pk}')
            return Response({'message':"Cost Center Level Deleted Successfully!"}, status=status.HTTP_200_OK)    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)