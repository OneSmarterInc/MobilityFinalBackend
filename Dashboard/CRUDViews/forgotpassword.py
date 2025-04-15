from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from ..Serializers.cat import catserializer
from authenticate.models import PortalUser
from rest_framework.permissions import IsAuthenticated

class ForgotPassswordView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,pk=None, *args, **kwargs):
        pass
    def post(self, request, *args, **kwargs):
        pass
    def put(self, request,pk, *args, **kwargs):
        pass
    def delete(self, request, pk, *args, **kwargs):
        pass