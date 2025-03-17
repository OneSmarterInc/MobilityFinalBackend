from django.urls import path
from .views import BatchView
urlpatterns = [
    path('', BatchView.as_view(), name='batch-detail-post'),
    path('<id>/', BatchView.as_view(), name='batch-update-delete'),

]