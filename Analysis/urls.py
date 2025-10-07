from django.urls import path
from .views import AnalysisView, download_analysis_xlsx_file, MultipleUploadView, AnalysisBotView, GetChatPdfView, GetSavingsPdfView
urlpatterns = [
    path('', AnalysisView.as_view(), name='analysis-list-create'),
    path('multiple/', MultipleUploadView.as_view(), name='multiple-analysis-list-create'),
    path('bot/<str:ChatType>/<int:pk>/', AnalysisBotView.as_view(), name='analysis-bot'),
    path('<str:pk>/', AnalysisView.as_view(), name='analysis-detail'),
    path('multiple/<str:pk>/', MultipleUploadView.as_view(), name='multiple-analysis-detail'),
    path('<str:pk>/download-xlsx/', download_analysis_xlsx_file.as_view(), name='download-analysis-xlsx'),
    path('get-chat-pdf/<str:pk>/', GetChatPdfView.as_view(), name='get-chat-pdf'),
    path('get-savings-pdf/<str:pk>/', GetSavingsPdfView.as_view(), name='get-savings-pdf'),
]
