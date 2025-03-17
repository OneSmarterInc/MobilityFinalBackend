from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.auth import login, logout
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from OnBoard.Company.models import Company
from rest_framework import status
from .serializers import RegisterSerializer, showUsersSerializer, UserLogSaveSerializer, UserLogShowSerializer, allDesignationsSerializer, CompanyShowSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import PortalUser, UserLogs

class RegisterView(APIView):

    def get(self, request, *args, **kwargs):
        allCompanies = Company.objects.all()
        Comser = CompanyShowSerializer(allCompanies, many=True)
        allDesignations = UserRoles.objects.all()
        ser = allDesignationsSerializer(allDesignations, many=True)
        return Response({"designations": ser.data, "companies" : Comser.data}, status=status.HTTP_200_OK)
    
    def post(self,request):
        data = request.data
        email = request.data['email']
        if PortalUser.objects.filter(email=email).exists():
            return Response({"message": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RegisterSerializer(data=data)
        try:
            if serializer.is_valid():
                user = serializer.save()

                saveuserlog(user, description=f'{user.username} registered successfully!')
                return Response({
                    'message' : 'User created successfully',
                    'status':True,
                    "data":serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({"message":str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
class LoginView(APIView):
    def post(self, request):
        data = request.data
        username = data.get("username")
        password = data.get("password")
        user = PortalUser.objects.filter(username=username).first()
        if not user:
            user = PortalUser.objects.filter(email=username).first()
        if user and user.check_password(password):
            login(request, user)
            refresh = RefreshToken.for_user(user)
            userser = showUsersSerializer(user)
            usrlogdesc = f'{user.username} logged in successfully!'
            saveuserlog(user, description=usrlogdesc)
            return Response({
                'message' : 'User logged in successfully',
                "logged_user" : userser.data,
                "access_token" : str(refresh.access_token),
                "refresh_token" : str(refresh),
            }, status=status.HTTP_200_OK)
        return Response({
            "message" : "Invalid Credentials"
        }, status=status.HTTP_400_BAD_REQUEST)
    
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id=None):
        if id is None:
            user = request.user
            allusers = PortalUser.objects.all().exclude(username=user)
            serializer = showUsersSerializer(allusers, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            user = PortalUser.objects.filter(username=id).first()
            if not user:
                user = PortalUser.objects.filter(email=id).first()
            if not user:
                return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            serializer = showUsersSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
    def delete(self, request, id):
        try:
            user = PortalUser.objects.get(id=id)
            user.delete()
            saveuserlog(request.user, description=f'{user.username} deleted successfully!')
            return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except PortalUser.DoesNotExist or Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)
    def put(self, request, id):
        try:
            user = PortalUser.objects.get(id=id)
            serializer = RegisterSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                saveuserlog(request.user, description=f'{user.username} updated successfully!')
                return Response({"message": "User updated successfully."}, status=status.HTTP_200_OK)
            
            return Response({"message": str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        except PortalUser.DoesNotExist or Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)
        
    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                saveuserlog(request.user, description=f'{serializer.data["username"]} registered successfully!')
                return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
            return Response({"message": str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class Logoutview(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            logdesc = f'{request.user.username} logged out successfully!'
            saveuserlog(request.user, description=logdesc)
            logout(request)
            return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            print(e)
            return Response({"message": "Error occurred: " + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
def saveuserlog(user, description):
    data = {
        "user": user.id,
        "description": description,
    }
    usrlogSer = UserLogSaveSerializer(data=data)
    if usrlogSer.is_valid():
        usrlogSer.save()
    else:
        print("Error saving userlog: " + str(usrlogSer.errors))
    
class UserLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        if id is None:
            userlogs = UserLogs.objects.all().order_by("created_at")
            serializer = UserLogShowSerializer(userlogs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            try:
                user = PortalUser.objects.filter(id=id).order_by('created_at').first()
                if not user:
                    user = PortalUser.objects.filter(id=id).first()
                if not user:
                    return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
                userlog = UserLogs.objects.filter(user=user.id)
                serializer = UserLogShowSerializer(userlog, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except UserLogs.DoesNotExist:
                return Response({"message": "User log not found."}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, id):
        try:
            userlog = UserLogs.objects.get(id=id)
            userlog.delete()
            return Response({"message": "User log deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except UserLogs.DoesNotExist or Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)
