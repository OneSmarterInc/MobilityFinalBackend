from django.urls import path
from .views import RegisterView, LoginView, ProfileView, Logoutview, UserLogView
urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('profile/', ProfileView.as_view()), 
    path('profile/<id>/', ProfileView.as_view()),
    path('logout/', Logoutview.as_view()), 
    path('user-logs/', UserLogView.as_view()),
    path('user-logs/<id>/', UserLogView.as_view()),

]   