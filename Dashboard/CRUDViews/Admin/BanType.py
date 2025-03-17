from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import BanType
from ...Serializers.AdminPage import BanTypeOperationSerializer, BanTypeShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog


class BanTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            ban_type = BanType.objects.get(name=pk)
            ser = BanTypeShowSerializer(ban_type)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        else:
            ban_types = BanType.objects.all()
            ser = BanTypeShowSerializer(ban_types, many=True)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        
    
    def post(self, request):
        ser = BanTypeOperationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'New Ban Type created: {ser.data["name"]}')
            return Response({"message" : "new BanType created successfully!", "data":ser.data}, status=status.HTTP_201_CREATED)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk):
        try:
            ban_type = BanType.objects.get(name=pk)
        except BanType.DoesNotExist:
            return Response({"message": 'Ban Type not found'}, status=status.HTTP_404_NOT_FOUND)
        ser = BanTypeOperationSerializer(ban_type, data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'Ban Type updated: {ser.data["name"]}')
            return Response({"message" : "BanType updated successfully", "data":ser.data}, status=status.HTTP_200_OK)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        try:
            ban_type = BanType.objects.get(name=pk)
            ban_type.delete()
            saveuserlog(request.user, description=f'Ban Type deleted: {pk}')
            return Response({'message':"Ban Type Deleted Successfully!"}, status=status.HTTP_200_OK)    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)