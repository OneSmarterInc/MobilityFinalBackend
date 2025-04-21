from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import BanStatus
from authenticate.views import saveuserlog
from ...Serializers.AdminPage import BanStatusOperationSerializer, BanStatusShowSerializer
from rest_framework.permissions import IsAuthenticated


class BanStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk is None:
            ban_status = BanStatus.objects.all()
            ser = BanStatusShowSerializer(ban_status, many=True)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        else:
            ban_status = BanStatus.objects.get(name=pk)
            ser = BanStatusShowSerializer(ban_status)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        if BanStatus.objects.filter(name=request.data["name"]).exists():
            return Response({"message": "Ban status with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = BanStatusOperationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, description=f'New Ban Status created: {serializer.data["name"]}')
            return Response({"message" : "new band status created successfully!", "data" : serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk):
        try:
            ban_status = BanStatus.objects.get(name=pk)
        except BanStatus.DoesNotExist:
            return Response({"message": 'Ban Status not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BanStatusOperationSerializer(ban_status, data=request.data)
        if serializer.is_valid():
            serializer.save()
            saveuserlog(request.user, description=f'Ban Status updated: {serializer.data["name"]}')
            return Response({"message" : "band status updated successfully!", "data":serializer.data}, status=status.HTTP_200_OK)
        return Response({"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        try:
            ban_status = BanStatus.objects.get(name=pk)
            ban_status.delete()
            saveuserlog(request.user, description=f'Ban Status deleted: {pk}')
            return Response({"message" : "Ban Status Deleted Successfully!"}, status=status.HTTP_200_OK)    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)