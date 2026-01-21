from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ...ModelsByPage.DashAdmin import Permission
from ...Serializers.AdminPage import PermissionOperationSerializer, PermissionShowSerializer
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from Batch.views import create_notification
from authenticate.views import saveuserlog

def is_superadmin(user):
    return not user.company

class PermissionView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk=None):
        try:
            if pk:
                permission = Permission.objects.get(name=pk)
                ser = PermissionShowSerializer(permission)
                return Response({"data" : ser.data}, status=status.HTTP_200_OK)
            else:

                print(is_superadmin(request.user))
                
                permissions = Permission.objects.all() if is_superadmin(request.user) else Permission.objects.exclude(Type__icontains="organization")

                ser = PermissionShowSerializer(permissions, many=True)
                print(ser.data)
                return Response({"data" : ser.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def post(self, request):
        if Permission.objects.filter(name=request.data["name"]).exists():
            return Response({"message": "permission with this name already exists!"}, status=status.HTTP_400_BAD_REQUEST)
        ser = PermissionOperationSerializer(data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, f"New permission added with name {ser.data['name']}")  # save user log for audit trail
            create_notification(request.user, f"New permission added with name {ser.data['name']}",request.user.company) 
            return Response({"message" : "new permission created successfully!", "data":ser.data}, status=status.HTTP_201_CREATED)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, pk):
        try:
            permission = Permission.objects.get(name=pk)
        except Permission.DoesNotExist:
            return Response({"message": 'Permission not found'}, status=status.HTTP_404_NOT_FOUND)
        ser = PermissionOperationSerializer(permission, data=request.data)
        if ser.is_valid():
            ser.save()
            saveuserlog(request.user, description=f'Permission updated: {ser.data["name"]}')
            # create_notification(request.user, description=f'Permission {ser.data["name"]} updated',company=request.user.company)
            return Response({"message" : "permission updated successfully!", "data":ser.data}, status=status.HTTP_200_OK)
        return Response({"message":ser.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            permission = Permission.objects.get(name=pk)
            permission.delete()
            saveuserlog(request.user, description=f'Permission {pk} deleted')
            # create_notification(request.user, description=f'Permission {pk} deleted',company=request.user.company)
            return Response({"message" : "permission deleted successfully!"}, status=status.HTTP_200_OK)
        except Permission.DoesNotExist:
            return Response({"message": 'Permission not found'}, status=status.HTTP_404_NOT_FOUND)
