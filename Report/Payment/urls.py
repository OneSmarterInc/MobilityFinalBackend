# urls.py
# for get_payment_report_by_due_date/
from django.urls import path
from .views import GetPaymentReportByDueDate
paymenturls = [
    path('get_payment_report_by_due_date/', GetPaymentReportByDueDate.as_view(), name='get_payment_report_by_due_date'),
]