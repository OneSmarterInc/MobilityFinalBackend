from django.urls import path
from .views import ViewReportView, UploadFileView

urlpatterns = [
    path('view-report/', ViewReportView.as_view(), name='view-report-detail'),
    path('view-report/<report_type>/', ViewReportView.as_view(), name='view-report-detail'),
    path('view-report/<report_type>/<sub_type>/', ViewReportView.as_view(), name='view-report-detail'),
    path('view-report/<pk>/', ViewReportView.as_view(), name='view-report-delete-update'),

    path('upload-report/', UploadFileView.as_view(), name='upload-file-detail'),
    path('upload-report/<report_type>/', UploadFileView.as_view(), name='upload-file-report-detail'),
    path('upload-report/<report_type>/<pk>/', UploadFileView.as_view(), name='upload-file-delete-update'),
]
