from django.urls import path
from .views import AnalysisView, download_analysis_xlsx_file
urlpatterns = [
    path('', AnalysisView.as_view(), name='analysis-list-create'),
    path('<str:pk>/', AnalysisView.as_view(), name='analysis-detail'),
    path('<str:pk>/download-xlsx/', download_analysis_xlsx_file.as_view(), name='download-analysis-xlsx')
]