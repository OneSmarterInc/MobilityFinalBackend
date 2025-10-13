from django.urls import path
from .views import RegisterView, LoginView, ProfileView, Logoutview, UserLogView
from .views import SendOTPView, VerifyOTPView, ForgotPassswordView, BulkUserUpload, verifyEmailView


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
]   
