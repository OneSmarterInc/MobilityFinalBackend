from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import EntryType
from ...Serializers.AdminPage import EntryTypeOperationSerializer, EntryTypeShowSerializer
from rest_framework.permissions import IsAuthenticated
from authenticate.views import saveuserlog


class EntryTypeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if pk:
            entry_type = EntryType.objects.get(name=pk)
            ser = EntryTypeShowSerializer(entry_type)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        else:
            entry_types = EntryType.objects.all()
            ser = EntryTypeShowSerializer(entry_types, many=True)
            return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        ser = EntryTypeOperationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'New Entry Type created: {ser.data["name"]}') 
            return Response({"message" : "new Entry Type created successfully!", "data":ser.data}, status=status.HTTP_201_CREATED)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk):
        try:
            entry_type = EntryType.objects.get(name=pk)
        except EntryType.DoesNotExist:
            return Response({"message": 'Entry Type not found'}, status=status.HTTP_404_NOT_FOUND)
        ser = EntryTypeOperationSerializer(entry_type, data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'Entry Type updated: {ser.data["name"]}')
            return Response({"message" : "EntryType updated successfully!", "data":ser.data}, status=status.HTTP_200_OK)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def delete(self, request, pk):
        try:
            entry_type = EntryType.objects.get(name=pk)
            entry_type.delete()
            saveuserlog(request.user, description=f'Entry Type deleted: {pk}')
            return Response({'message':"Entry Type Deleted Successfully!"}, status=status.HTTP_200_OK)    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)