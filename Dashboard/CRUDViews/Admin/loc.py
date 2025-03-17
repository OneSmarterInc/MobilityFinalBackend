from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import ManuallyAddedLocation
from ...Serializers.AdminPage import LocOperationSerializer, LocShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog


class LocView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk=None):
        if pk:
            location = ManuallyAddedLocation.objects.get(name=pk)
            ser = LocShowSerializer(location)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        else:
            locations = ManuallyAddedLocation.objects.all()
            ser = LocShowSerializer(locations, many=True)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        ser = LocOperationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'New Location created: {ser.data["name"]}')  # Save user log for auditing purposes.
            return Response({"message" : "new location created successfully!", "data" : ser.data}, status=status.HTTP_201_CREATED)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk):
        try:
            location = ManuallyAddedLocation.objects.get(name=pk)
        except ManuallyAddedLocation.DoesNotExist:
            return Response({"message": 'Location not found'}, status=status.HTTP_404_NOT_FOUND)
        ser = LocOperationSerializer(location, data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'Location updated: {ser.data["name"]}')
            return Response({"message" : "Location updated successfully!", "data":ser.data}, status=status.HTTP_200_OK)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            location = ManuallyAddedLocation.objects.get(name=pk)
            location.delete()
            saveuserlog(request.user, description=f'Location deleted: {pk}')
            return Response({'message':"Location Deleted Successfully!"}, status=status.HTTP_200_OK)    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
