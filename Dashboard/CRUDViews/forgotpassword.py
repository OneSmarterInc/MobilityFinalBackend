from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.cat import catserializer
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password, check_password
class ForgotPassswordView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        pass
    def post(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(user.password)
        print(data)
        old = data.get('old_password')
        new = data.get('new_password')
        confirm = data.get('confirm_password')
        if new != confirm:
            return Response({"message":"new password and confirm password not matched!"}, status=status.HTTP_400_BAD_REQUEST)
        print(old, new, confirm)
        if not user.check_password(old):
            return Response({"message":"old password not matched!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user.password = make_password(new)
            user.save()
            return Response({"message":"password updated successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request,pk, *args, **kwargs):
        pass
    def delete(self, request, pk, *args, **kwargs):
        pass