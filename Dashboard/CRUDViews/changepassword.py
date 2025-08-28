from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password, check_password
from authenticate.views import saveuserlog
class ChangePassswordView(APIView):
    permission_classes = [IsAuthenticated]

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
            saveuserlog(request.user, f"password updated for account {user.email}")
            return Response({"message":"password updated successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message":"unable to update password."}, status=status.HTTP_400_BAD_REQUEST)

