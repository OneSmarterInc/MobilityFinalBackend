from django.urls import path
from .views import ViewBill, ViewBillBaseline
viewbill_urls = [
    path('view-bill/', ViewBill.as_view(), name='viewbill-list-create'),
    path('view-bill/<int:pk>/', ViewBill.as_view(), name='viewbill-detail'),
    path('view-bill/view-bill-baseline/', ViewBillBaseline.as_view(), name='viewbill-baseline'),
    path('view-bill/view-bill-baseline/<int:pk>/', ViewBillBaseline.as_view(), name='viewbill-baseline-detail'),
]