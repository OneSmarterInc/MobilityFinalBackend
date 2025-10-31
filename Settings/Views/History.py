from ..ser import saveBanhistorySerializer, saveWirelesshistorySerializer

def save_ban_history(ban, action,user,uploadID=None, onboardID=None):
    data = {
        "banUploaded":uploadID,
        "banOnboarded":onboardID,
        "account_number":ban,
        "user":user,
        "action":action
    }
    ser = saveBanhistorySerializer(data=data)
    if ser.is_valid():
        ser.save()
    else:
        print("Error saving ban history: " + str(ser.errors))

def save_wireless_history(wn, action,user,uploadID=None, onboardID=None):
    data = {
        "banUploaded":uploadID,
        "banOnboarded":onboardID,
        "wireless_number":wn,
        "user":user,
        "action":action
    }
    ser = saveWirelesshistorySerializer(data=data)
    if ser.is_valid():
        ser.save()
    else:
        print("Error saving ban history: " + str(ser.errors))
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from authenticate.views import saveuserlog
from rest_framework.permissions import IsAuthenticated
from ..ser import showBanhistorySerializer, showWirelesshistorySerializer
from ..models import BanHistory, WirelessHistory

class BanHistoryView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, ban, *args, **kwargs):
        try:
            allhistory = BanHistory.objects.filter(account_number=ban).order_by('-timestamp')
            ser = showBanhistorySerializer(allhistory, many=True)

            return Response({"data":ser.data},status=status.HTTP_200_OK)
        except Exception:
            return Response({"message":f"Unable to fetch history of ban {ban}"}, status=status.HTTP_400_BAD_REQUEST)

class WirelessHistoryView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, wn, *args, **kwargs):
        try:
            allhistory = WirelessHistory.objects.filter(wireless_number=wn).order_by('-timestamp')
            ser = showWirelesshistorySerializer(allhistory, many=True)

            return Response({"data":ser.data},status=status.HTTP_200_OK)
        except Exception:
            return Response({"message":f"Unable to fetch history of wireless number {wn}"}, status=status.HTTP_400_BAD_REQUEST)