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
            return Response(
                {"message": "Email address is already in use."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RegisterSerializer(data=data)
        try:
            if serializer.is_valid():
                user = serializer.save()

                saveuserlog(user, description=f'{user.email} registered successfully!')
                return Response({
                    'message' : 'User created successfully',
                    'status':True,
                    "data":serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({"message":"Unable to register user."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({"message": "Internal Server Error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
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
            usrlogdesc = f'{user.email} logged in successfully!'
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
            user = PortalUser.objects.filter(id=id).first()
            email = user.email
            if not user:
                return Response({"message": "user not found."}, status=status.HTTP_404_NOT_FOUND)
            user.delete()
            saveuserlog(request.user, description=f'{email} deleted successfully!')
            return Response({"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except PortalUser.DoesNotExist or Exception as e:
            return Response({"message": "Unable to delete user."}, status=status.HTTP_404_NOT_FOUND)
    def put(self, request, id):
        try:
            user = PortalUser.objects.get(id=id)
            serializer = RegisterSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                saveuserlog(request.user, description=f'{user.email} updated successfully!')
                return Response({"message": "User updated successfully."}, status=status.HTTP_200_OK)
            
            return Response({"message": "Unable to update user."}, status=status.HTTP_400_BAD_REQUEST)
        except PortalUser.DoesNotExist or Exception as e:
            return Response({"message": "Internal Server Error!"}, status=status.HTTP_404_NOT_FOUND)
        
    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                saveuserlog(request.user, description=f'{serializer.data["email"]} registered successfully!')
                return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
            return Response({"message": "unable to register user."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "Internal Server Error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class Logoutview(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            logdesc = f'{request.user.email} logged out successfully!'
            saveuserlog(request.user, description=logdesc)
            logout(request)
            return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            print(e)
            return Response({"message": "Error occurred: " + "unable to logout."}, status=status.HTTP_400_BAD_REQUEST)
        
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
            userlog = UserLogs.objects.filter(id=id).first()
            userlog.delete()
            return Response({"message": "User log deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except UserLogs.DoesNotExist or Exception as e:
            return Response({"message": "Unable to delete user log"}, status=status.HTTP_404_NOT_FOUND)


from .serializers import EmailSerializer, OTPVerifySerializer
from .models import EmailOTP
import random
from sendmail import send_generic_mail

class SendOTPView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # get or create user
            user = PortalUser.objects.filter(email=email).first()
            if not user:
                return Response({"message":"User not found!"},status=status.HTTP_400_BAD_REQUEST)

            # generate 6 digit OTP
            otp = str(random.randint(100000, 999999))

            # store OTP in DB
            EmailOTP.objects.update_or_create(
                user=user, defaults={"otp": otp, "is_verified": False}
            )

            # send email
            send_generic_mail(
            
                subject="Your OTP Code",
                body=f"Your OTP is {otp}",
                receiver_mail=email
                
            )
            saveuserlog(request.user, f"OTP for password update request mailed to {email}")

            return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            otp = serializer.validated_data["otp"]

            try:
                user = PortalUser.objects.get(email=email)
                email_otp = EmailOTP.objects.get(user=user)

                if email_otp.otp == otp:
                    email_otp.is_verified = True
                    email_otp.save()
                    saveuserlog(request.user, f"OTP for password update request verified by {email}")
                    return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

            except (User.DoesNotExist, EmailOTP.DoesNotExist):
                return Response({"message": "User/OTP not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from django.contrib.auth.hashers import make_password, check_password

class ForgotPassswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        user = request.user
        print(user.password)
        print(data)
        new = data.get('new_password')
        confirm = data.get('confirm_password')
        print(new, confirm)
        if new != confirm:
            return Response({"message":"new password and confirm password not matched!"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user.password = make_password(new)
            user.save()
            saveuserlog(request.user, f"password updated for account {user.email}")
            return Response({"message":"password updated successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message":"unable to update password."}, status=status.HTTP_400_BAD_REQUEST)