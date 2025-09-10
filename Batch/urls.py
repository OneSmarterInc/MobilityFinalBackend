# urls.py (order matters!)
from django.urls import path
from .views import BatchView, BatchAutomationViewSet,email_config_list,email_config_detail,EmailConfigurationViewSet
from .views import notifications_by_company, delete_notification

urlpatterns = [
      
    path(
        'email-configs/verify/',
        EmailConfigurationViewSet.as_view({'post': 'verify'}),
        name='email_config_verify',
    ), 
     path('email-configs/', email_config_list, name='email_config_list'),
    path('email-configs/<int:pk>/', email_config_detail, name='email_config_detail'),
   
    path(
        'automation/batch/',
        BatchAutomationViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='batch-automation-list-create'
    ),
    path('automation/batch/<int:pk>/', BatchAutomationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),

    path('<str:org>/', BatchView.as_view(), name='batch-detail-post'),
    path('<str:org>/<int:id>/', BatchView.as_view(), name='batch-update-delete'),
    path("notifications/", notifications_by_company, name="notifications-by-company"),
    path("notifications/<int:pk>/", delete_notification, name="notifications-delete"),
    
   
]
