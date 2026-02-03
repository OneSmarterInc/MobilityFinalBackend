from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import login, logout
from Dashboard.ModelsByPage.DashAdmin import UserRoles
from OnBoard.Company.models import Company
from rest_framework import status
from .serializers import RegisterSerializer, showUsersSerializer, UserLogSaveSerializer, UserLogShowSerializer, allDesignationsSerializer, CompanyShowSerializer, userSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .models import PortalUser, UserLogs
from OnBoard.Organization.models import Organizations
from OnBoard.Ban.models import UniquePdfDataTable
from Dashboard.ModelsByPage.DashAdmin import Vendors
from rest_framework.decorators import api_view, permission_classes
class RegisterView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        allCompanies = Company.objects.all()
        Comser = CompanyShowSerializer(allCompanies, many=True)
        allDesignations = UserRoles.objects.filter(company=request.user.company).exclude(id=request.user.designation.id)
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

        data['string_password'] = data.get('password')
        data['temp_password'] = data.get('password')
        try:
            serializer = RegisterSerializer(data=data)
            if serializer.is_valid():
                user = serializer.save()
                add_wireless_numbers({user.email : user.mobile_number.strip()})
                saveuserlog(request.user, description=f'{user.email} registered successfully!')
                create_notification(request.user, msg=f'{user.email} registered successfully!', company=request.user.company)
                return Response({
                    'message' : 'User created successfully',
                    'status':True,
                    "data":serializer.data
                }, status=status.HTTP_201_CREATED)
            print(serializer.errors)
            return Response(
                {"message": "User registration failed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            print(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
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
            if not user.is_active:
                return Response({"message": "Authentication error: You are no longer an active user."},status=status.HTTP_400_BAD_REQUEST)
            if user.last_login and temp_check:
                return Response({"message": "You must change your password using the 'Forgot Password' option before logging in."}, status=status.HTTP_400_BAD_REQUEST)

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
            try:
                id=int(id)
                user = PortalUser.objects.filter(id=id).first()
            except:
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
            return Response(
                {
                    "message": "User not found or could not be deleted."
                },
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, id):
        try:
            user = PortalUser.objects.get(id=id)
            print("user==",user,user.username)
             
            serializer = userSerializer(user, data=request.data,partial=True)
            if serializer.is_valid():
                serializer.save()
                saveuserlog(request.user, description=f'{user.email} updated successfully!')
                # create_notification(request.user, msg=f'{user.email} updated successfully!', company=request.user.company)
                return Response({"message": "User updated successfully."}, status=status.HTTP_200_OK)
            print(serializer.errors)
            return Response({"message": "Unable to update user."}, status=status.HTTP_400_BAD_REQUEST)
        except PortalUser.DoesNotExist or Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                add_wireless_numbers({user.email : user.mobile_number.strip()})
                em = user.email
                saveuserlog(request.user, description=f'{em} registered successfully!')
                create_notification(request.user, msg=f'{em} registered successfully!', company=request.user.company)
                return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
            return Response({"message": "unable to register user."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_org_users(request, org):
    orgObj = Organizations.objects.filter(id=org).first()
    if not orgObj:
        return Response({"message": "organization not found."}, status=status.HTTP_400_BAD_REQUEST)
    users = PortalUser.objects.filter(organization=orgObj)
    ser = showUsersSerializer(users, many=True)
    return Response({"data":ser.data},status=status.HTTP_200_OK)

from .signals import UserSignalThread

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def resend_notification(request,id):
    try:instance = PortalUser.objects.get(pk=id)
    except PortalUser.DoesNotExist: return Response({"message":"User not found!"},status=status.HTTP_404_NOT_FOUND)
    try:
        UserSignalThread(
            instance=instance,
            company=instance.company.Company_name if instance.company else None,
            organization=instance.organization.Organization_name if instance.organization else None,
            role=instance.designation.name if instance.designation else None,
            username=instance.username,
            email=instance.email,
            pwd=instance.string_password
        ).start()
        return Response({"message":"Notification sent!"},status=status.HTTP_200_OK)
    except Exception:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
def saveuserlog(user, description):
    if not user.is_authenticated:
        return
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

            print("OTP==",otp)

            send_generic_mail(
            
                subject="Your OTP Code",
                body=f"Your OTP is {otp}",
                receiver_mail=email
                
            )
            print(request.user)
            if request.user.is_authenticated :saveuserlog(request.user, f"OTP for password update request mailed to {email}")
            
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
                    if request.user.is_authenticated:saveuserlog(request.user, f"OTP for password update request verified by {email}")
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
            if request.user.is_authenticated: saveuserlog(request.user, f"password updated for account {user.email}")
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
                user = ser.save()
                add_wireless_numbers({user.email : user.mobile_number.strip()})

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
        return Response(
            {
                "message": "Users added successfully in bulk."
            },
            status=status.HTTP_201_CREATED
        )

    
from .serializers import banUsersSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portal_employees(request, org, *args, **kwargs):
    org = Organizations.objects.filter(id=org).first()
    if not org:
        return Response(
            {"message": "Organization not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    params = request.GET
    vendor = params.get("vendor")
    ban = params.get("ban")
    role = params.get("role")

    # -------- Portal users query --------
    portal_filters = {"organization": org}

    if vendor:
        vendor_obj = org.vendors.filter(name=vendor).first()
        if not vendor_obj:
            return Response(
                {"message": "Vendor not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        portal_filters["vendor"] = vendor_obj

    if ban: portal_filters["account_number"] = ban

    if role:
        role_obj = UserRoles.objects.filter(
            organization=org, name=role
        ).first()
        portal_filters["designation"] = role_obj

    _portalusers = PortalUser.objects.filter(**portal_filters)

    # -------- BAN users query --------
    _ban_users = UniquePdfDataTable.objects.exclude(banUploaded=None,banOnboarded=None).filter(
        sub_company=org.Organization_name
    )

    if vendor:_ban_users = _ban_users.filter(vendor=vendor)

    if ban:_ban_users = _ban_users.filter(account_number=ban)

    # Serialize
    _ban_users_data = banUsersSerializer(_ban_users, many=True).data
    _portalusers_data = showUsersSerializer(_portalusers, many=True).data

    # Build portal lookup: email -> role
    portal_lookup = {}

    for u in _portalusers_data:
        email = u.get("email")
        if email:
            portal_lookup[email.strip().lower()] = {
                "role": u.get("role") or u.get("designation")
            }

    # Annotate BAN users
    for user in _ban_users_data:
        email = user.get("User_email")  # as per your serializer field

        if email:
            key = email.strip().lower()
            portal_user = portal_lookup.get(key)

            if portal_user:
                user["is_onboarded"] = True
                user["role"] = portal_user["role"]
            else:
                user["is_onboarded"] = False
                user["role"] = None
        else:
            user["is_onboarded"] = False
            user["role"] = None

    return Response(
        {"data": _ban_users_data},
        status=status.HTTP_200_OK
    )

from collections import defaultdict


from django.conf import settings

@api_view(["GET"])
def get_sample_file(request):
    org = request.GET.get("organization", None)
    request_type = request.GET.get("request_type", None)
    if request_type == "onboard":
        pdf_path = "Excel_ban_onboard_sample.xlsx"
    elif request_type == "upload_bill":
        pdf_path = "Excel_bill_upload_sample.xlsx"
    elif request_type == "location":
        pdf_path = "Bulk_location_upload.xlsx"
    elif request_type == "inventory":
        pdf_path = "Bulk_inventory_update_sample.xlsx"
    elif request_type == "user":
        pdf_path = "Bulk_user_upload_sample.xlsx"
    elif request_type == "requests":
        pdf_path = "Bulk_request_upload_sample.xlsx"
    elif request_type == "accessory_requests":
        pdf_path = "Bulk_accessory_requests_sample.xlsx"
    elif request_type == "unbilled_excel_sample":
        pdf_path = "Unbilled_excel_sample.xlsx"
    elif request_type == "billed_excel_sample":
        pdf_path = "Billed_excel_sample.xlsx"
    else:
        return Response(
            {"message": "Invalid file request!"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    absolute_url = request.build_absolute_uri(
        settings.STATIC_URL + "SampleDocs/" + pdf_path
    )

    if org:
        safe_org = str(org).replace(" ", "_")
        file_name = f"{safe_org}_{pdf_path}"
    else:
        file_name = pdf_path
    print(file_name)
    return Response(
        {
            "pdf_url": absolute_url,
            "file_name": file_name,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_wireless_status(request,id,*args,**kwargs):
    try:
        emp = EmployeeWirelessNumber.objects.get(id=id)
    except EmployeeWirelessNumber.DoesNotExist:
        return Response({"message":"Wireless number not found!"},status=status.HTTP_404_NOT_FOUND)
     
    emp.is_active = False if emp.is_active else True
    emp.save()
    return Response({"message":"Employee wireless status updated."},status=status.HTTP_200_OK)

def partition_username(raw: str):
    if not raw:
        return "", "", ""

    raw = raw.strip().lower()

    if "@" in raw:
        first, _, last = raw.partition("@")
        return (
            f"{first}_{last}" if last else first,
            first,
            last,
        )

    parts = raw.split()
    first = parts[0]
    last = parts[1] if len(parts) > 1 else ""
    return "_".join(parts), first, last

from django.db import transaction

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def onboard_ban_employees(request, org, *args, **kwargs):
    org = Organizations.objects.filter(id=org).first()
    if not org:
        return Response({"message": "Organization not found"}, status=404)

    ids = request.data.get("ids")
    if not ids:
        return Response({"message": "ids required"}, status=400)

    vendor_name = request.GET.get("vendor")
    ban = request.GET.get("ban")
    role_name = request.GET.get("role")

    vendor = (
        org.vendors.filter(name=vendor_name).only("id").first()
        if vendor_name else None
    )
    if vendor_name and not vendor:
        return Response({"message": "Vendor not found"}, status=400)

    role = (
        UserRoles.objects
        .filter(organization=org, name=role_name)
        .only("id")
        .first()
        if role_name else None
    )

    users_qs = (
        UniquePdfDataTable.objects
        .filter(id__in=ids)
        .values_list("User_email", "wireless_number", "user_name")
    )

    temp_pass = "1234"
    encrypted = make_password(temp_pass)

    wireless_map = defaultdict(set)

    with transaction.atomic():
        for email, mobile, name in users_qs:
            if not email:
                continue

            email = email.strip().lower()
            username, first, last = partition_username(name or email)

            user, created = PortalUser.objects.get_or_create(
                email=email,
                defaults={
                    "username": username,
                    "company": org.company,
                    "organization": org,
                    "password": encrypted,
                    "temp_password": encrypted,
                    "string_password": temp_pass,
                }
            )

            # Update fields even if user exists
            user.mobile_number = mobile
            user.vendor = vendor
            user.account_number = ban
            user.designation = role
            user.first_name = first
            user.last_name = last
            user.save()

            if mobile:
                wireless_map[email].add(mobile.strip())

        add_wireless_numbers(wireless_map)

    return Response(
        {"message": "Ban users onboarded successfully."},
        status=status.HTTP_200_OK,
    )


from .models import EmployeeWirelessNumber
def add_wireless_numbers(email_wireless_map):
    if not email_wireless_map:
        return

    # 1. Normalise input: ensure list of numbers per email
    normalized_map = {}
    for email, nums in email_wireless_map.items():
        if isinstance(nums, str):
            normalized_map[email] = [nums]
        elif isinstance(nums, (list, tuple, set)):
            normalized_map[email] = list(nums)
        else:
            continue  # skip invalid formats safely

    if not normalized_map:
        return

    # 2. Fetch users
    users = PortalUser.objects.filter(
        email__in=normalized_map.keys()
    ).only("id", "email")

    user_map = {u.email: u.id for u in users}

    # 3. Collect all wireless numbers
    numbers = {
        num
        for nums in normalized_map.values()
        for num in nums
    }

    # 4. Find existing numbers
    existing = set(
        EmployeeWirelessNumber.objects
        .filter(number__in=numbers)
        .values_list("number", flat=True)
    )

    # 5. Prepare bulk create objects
    objs = [
        EmployeeWirelessNumber(
            user_id=user_map[email],
            number=num
        )
        for email, nums in normalized_map.items()
        if email in user_map
        for num in nums
        if num not in existing
    ]

    # 6. Bulk insert
    EmployeeWirelessNumber.objects.bulk_create(
        objs,
        ignore_conflicts=True
    )

