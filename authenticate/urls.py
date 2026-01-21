from django.urls import path
from .views import RegisterView, LoginView, ProfileView, Logoutview, UserLogView
from .views import SendOTPView, VerifyOTPView, ForgotPassswordView, BulkUserUpload, verifyEmailView, get_org_users,portal_employees, onboard_ban_employees,update_wireless_status,get_sample_file,resend_notification


urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('profile/', ProfileView.as_view()), 
    path('profile/<id>/', ProfileView.as_view()),
    path('logout/', Logoutview.as_view()), 
    path('user-logs/', UserLogView.as_view()),
    path('user-logs/<id>/', UserLogView.as_view()),
    path('verify-email/', verifyEmailView.as_view(), name='verify-email'),
    path("send-otp/", SendOTPView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("forgot-password/", ForgotPassswordView.as_view(), name="forgot-password"),
    path("bulk-users-upload/", BulkUserUpload.as_view(), name="bulk-upload"),
    path("org-users/<int:org>/", get_org_users, name="org-users"),
    path("portal-employees/<int:org>/", portal_employees, name="portal-employees"),
    path("onboard-ban-employees/<int:org>/", onboard_ban_employees, name="onboard-ban-employees"),
    path("update-employee-wireless-status/<int:id>/", update_wireless_status, name="update-employee-wireless-status"),
    path("get-sample-file", get_sample_file, name="get-sample-file"),
    path("resend-notification/<int:id>/", resend_notification, name="get-sample-file"),
]   
