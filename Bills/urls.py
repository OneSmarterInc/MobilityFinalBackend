"""
URL configuration for Bills project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
]

my_app_urlpatterns = [
    path('auth/', include('authenticate.urls')),
    path('dashboard/', include('Dashboard.urls')),
    path('onboard/', include('OnBoard.urls')),
    path('inventory/', include('Inventory.urls')),
    path('analysis/', include('Analysis.urls')),
    path('view/', include('View.urls')),
    path('batch/', include('Batch.urls')),
    path('report/', include('Report.urls')),
    path('settings/', include('Settings.urls')),
]


urlpatterns += my_app_urlpatterns



from django.conf.urls.static import static
from django.conf import settings

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
