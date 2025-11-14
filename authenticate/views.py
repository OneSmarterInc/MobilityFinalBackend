from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import login, logout
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from OnBoard.Company.models import Company
from rest_framework import status
from .serializers import RegisterSerializer, showUsersSerializer, UserLogSaveSerializer, UserLogShowSerializer, allDesignationsSerializer, CompanyShowSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import PortalUser, UserLogs
from OnBoard.Organization.models import Organizations
from Dashboard.ModelsByPage.DashAdmin import Vendors
from rest_framework.decorators import api_view, permission_classes
class RegisterView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        allCompanies = Company.objects.all()
        Comser = CompanyShowSerializer(allCompanies, many=True)
        allDesignations = UserRoles.objects.exclude(id=request.user.designation.id).filter(company=request.user.company, organization=request.user.organization)
        ser = allDesignationsSerializer(allDesignations, many=True)
        return Response({"designations": ser.data, "companies" : Comser.data}, status=status.HTTP_200_OK)
    
    def post(self,request):
        data = request.data.copy()
        email = request.data['email']
        if PortalUser.objects.filter(email=email).exists():
            return Response(
                {"message": "Email address is already in use."},
                status=status.HTTP_400_BAD_REQUEST
            )
        print(data)
        # orgName = data.get('organization')
        # if orgName:
        #     orgObj = Organizations.objects.filter(Organization_name=orgName).first()
        # data['organization'] = orgObj.id if orgObj else None
        data['string_password'] = data.get('password')
        data['temp_password'] = data.get('password')
        try:
            serializer = RegisterSerializer(data=data)
            if serializer.is_valid():
                user = serializer.save()
                saveuserlog(request.user, description=f'{user.email} registered successfully!')
                create_notification(request.user, msg=f'{user.email} registered successfully!', company=request.user.company)
                return Response({
                    'message' : 'User created successfully',
                    'status':True,
                    "data":serializer.data
                }, status=status.HTTP_201_CREATED)
            print(serializer.errors)
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
        if not user:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # print(password,check_password(password, user.temp_password))
        temp_check = check_password(password, user.temp_password) if user and user.temp_password else False

        if user and user.check_password(password):
            # if user.last_login and temp_check:
            #     return Response({"message": "You must change your password using the 'Forgot Password' option before logging in."}, status=status.HTTP_400_BAD_REQUEST)

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
            # create_notification(request.user, msg=f'{email} deleted successfully!', company=request.user.company)
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
                # create_notification(request.user, msg=f'{user.email} updated successfully!', company=request.user.company)
                return Response({"message": "User updated successfully."}, status=status.HTTP_200_OK)
            
            return Response({"message": "Unable to update user."}, status=status.HTTP_400_BAD_REQUEST)
        except PortalUser.DoesNotExist or Exception as e:
            return Response({"message": "Internal Server Error!"}, status=status.HTTP_404_NOT_FOUND)
        
    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                em = serializer.data["email"]
                saveuserlog(request.user, description=f'{em} registered successfully!')
                create_notification(request.user, msg=f'{em} registered successfully!', company=request.user.company)
                return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
            return Response({"message": "unable to register user."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "Internal Server Error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])
def get_org_users(request, org):
    orgObj = Organizations.objects.filter(id=org).first()
    if not orgObj:
        return Response({"message": "organization not found."}, status=status.HTTP_400_BAD_REQUEST)
    users = PortalUser.objects.filter(organization=orgObj)
    ser = showUsersSerializer(users, many=True)
    return Response({"data":ser.data},status=status.HTTP_200_OK)

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
        "organization":user.organization.id if user.organization else None,
        "description": description,
    }
    print(data)
    usrlogSer = UserLogSaveSerializer(data=data)
    if usrlogSer.is_valid():
        usrlogSer.save()
    else:
        print("Error saving userlog: " + str(usrlogSer.errors))

from Batch.ser import NotificationSaveSerializer
from rest_framework.decorators import api_view, permission_classes

def create_notification(user, msg, company=None):
    data={
        "company_key":company.id if company else None,
        "company":company.Company_name if company else "",
        "user":user.id if user else None,
        "description":msg
    }
    print(data)
    ser = NotificationSaveSerializer(data=data)
    if ser.is_valid():
        ser.save()
    else:
        print("Error saving notification",ser.errors)
    
class UserLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        org = request.user.organization
        if id is None:
            userlogs = UserLogs.objects.all() if not org else UserLogs.objects.filter(organization=org)
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

class verifyEmailView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            if PortalUser.objects.filter(email=email).exists():
                return Response({"message": "Email exists"}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Email does not exist"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

            except (user.DoesNotExist, EmailOTP.DoesNotExist):
                return Response({"message": "User/OTP not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from django.contrib.auth.hashers import make_password, check_password

class ForgotPassswordView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        
        email = data.get('email')
        user = PortalUser.objects.filter(email=email).first()
        if not user:
            return Response({"message":"User not found!"}, status=status.HTTP_400_BAD_REQUEST)
        new = data.get('new_password')
        confirm = data.get('confirm_password')
        if new != confirm:
            return Response({"message":"new password and confirm password not matched!"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user.password = make_password(new)
            user.save()
            saveuserlog(request.user, f"password updated for account {user.email}")
            # create_notification(request.user, f"password updated for account {user.email}")
            return Response({"message":"password updated successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message":"unable to update password."}, status=status.HTTP_400_BAD_REQUEST)
        
import pandas as pd
from addon import parse_until_dict
from sendmail import send_custom_email
class BulkUserUpload(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request,*args,**kwargs):
        existance = []
        data = request.data.copy()
        file = data.get('file')
        df = pd.read_excel(file, index_col=False)
        mapping = parse_until_dict(data.get('mapping'))
        mapping_inverted = {v: k for k, v in mapping.items()}
        df = df.rename(columns=(mapping_inverted))
        company = data.get('company')
        if not company:
            return Response({"message":"Company Required"},status=status.HTTP_400_BAD_REQUEST)
        organization = data.get('organization')
        if not organization:
            return Response({"message": "organization not found."}, status=status.HTTP_400_BAD_REQUEST)
        vendor = data.get('vendor')
        if not vendor:
            return Response({"message": "vendor not found."}, status=status.HTTP_400_BAD_REQUEST)
        ban = data.get('ban')
        usertpe = data.get('usertype')
        if not usertpe:
            return Response({"message":"Usertype Required"},status=status.HTTP_400_BAD_REQUEST)
        passw = '1234'
        df['company'] = company
        df["organization"] = organization
        df["vendor"] = vendor
        df["account_number"] = ban
        df['designation'] = usertpe
        df["username"] = df["email"].str.split("@").str[0]
        df['temp_password'] = passw
        df['string_password'] = passw
        df['password'] = passw
        df['password2'] = passw

        records = df.to_dict(orient="records")
        total_len = len(records)

        for record in records:
            email = record.get('email')
            if PortalUser.objects.filter(email=email).exists(): existance.append(email)
        records = [rec for rec in records if rec["email"] not in existance] if existance else records
        for record in records:
            ser = RegisterSerializer(data=record)
            if ser.is_valid():
                ser.save()
        sub = "Bulk User Upload"
        email = request.user.email
        existing_emails = "\n".join(existance)
        if existance:
            msg = f"""
            Hello {request.user.username},

            Bulk user upload completed with some issues.

            📌 {len(records)} out of {total_len} users were registered successfully.
            ⚠️ The following {len(existance)} user(s) already exist in the system:

            {existing_emails}

            Regards,
            Team Mobility
            """
        else:
            msg = f"""
            Hello {request.user.username},

            Bulk user upload completed successfully.

            📌 All {total_len} users were registered successfully.

            Regards,
            Team Mobility
            """
        send_custom_email(company=company, to=email, subject=sub, body_text=msg)

        saveuserlog(request.user, description=f'{request.user.email} uploaded bulk users!')
        return Response({"message":"User added in bulk successfully!"},status=status.HTTP_201_CREATED)