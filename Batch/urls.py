from django.urls import path
from .views import BatchView
urlpatterns = [
    path('<str:org>/', BatchView.as_view(), name='batch-detail-post'),
    path('<str:org>/<id>/', BatchView.as_view(), name='batch-update-delete'),

]