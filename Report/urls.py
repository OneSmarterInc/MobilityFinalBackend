from django.urls import path
from .Payment.urls import paymenturls
urlpatterns = []
# urlpatterns = [
#     path('view-report1/', ViewReportView.as_view(), name='view-report-detail'),
#     path('view-report1/<report_type>/', ViewReportView.as_view(), name='view-report-detail'),
#     path('view-report1/<report_type>/<sub_type>/', ViewReportView.as_view(), name='view-report-detail'),
#     path('view-report1/<pk>/', ViewReportView.as_view(), name='view-report-delete-update'),

#     path('upload-report1/', UploadFileView.as_view(), name='upload-file-detail'),
#     path('upload-report1/<report_type>/', UploadFileView.as_view(), name='upload-file-report-detail'),
#     path('upload-report1/<report_type>/<pk>/', UploadFileView.as_view(), name='upload-file-delete-update'),
# ]
urlpatterns.extend(paymenturls)


from .Views.uploadbilled import UploadBilledReportView
from .Views.uploadunbilled import UploadUnbilledReportView
from .Views.viewbilled import ViewBilledReportView
from .Views.viewunbilled import ViewUnbilledReportView
from .views import GetReportDataView
# from .Views.viewunbilled import ViewUnbilledReportView
newurlspatterns = [

    # View Report URLs
    # path('view-report/unbilled/<sub_type>/'),
    path('view-report/billed/', view=ViewBilledReportView.as_view(), name='view-billed-report-detail'),
    path('view-report/billed/<sub_type>/', view=ViewBilledReportView.as_view(), name='view-billed-report-detail'),
    path('view-report/unbilled/', view=ViewUnbilledReportView.as_view(), name='view-unbilled-report-detail'),
    path('view-report/unbilled/<sub_type>/', view=ViewUnbilledReportView.as_view(), name='view-unbilled-report-detail'),

    # path('view-report/unbilled/<pk>/'),
    # path('view-report/billed/<pk>/'),


    # Upload Report URLs
    path('upload-report/unbilled/', view=UploadUnbilledReportView.as_view(), name='upload-unbilled-report'),
    path('upload-report/billed/', view=UploadBilledReportView.as_view(), name='upload-billed-report'),
    path('upload-report/unbilled/<pk>/', view=UploadUnbilledReportView.as_view(), name='upload-unbilled-report-detail-delete'),
    
    path('upload-report/billed/<pk>/', view=UploadBilledReportView.as_view(), name='upload-billed-report-detail-delete'),
    path('get-report-initials/', view=GetReportDataView.as_view(), name='get-report-data'),
]
urlpatterns.extend(newurlspatterns)
