from django.urls import path
from .views import ViewBill
viewbill_urls = [
    path('view-bill/', ViewBill.as_view(), name='viewbill-list-create'),
    path('view-bill/<int:pk>/', ViewBill.as_view(), name='viewbill-detail'),

]