from django.urls import path
from .views import   BaselineDetailView,TrackingAnalyticsView,RequestsAnalyticsView,BaselineAnalyticsView,BASavingsTimeSeriesView, BATopSavingsView,BAOptimizationSummaryView,BAUsageSummaryView,RequestSummaryView,BillSummaryView,BillExtremesView,BillTotalsView,BillStatusBreakdownView,BillTimeSeriesView,AnalysisDashboardView,AnalysisLinesView,AnalysisView, download_analysis_xlsx_file, MultipleUploadView, AnalysisBotView, GetChatPdfView, GetSavingsPdfView
urlpatterns = [
    
    # User Dashboard
     path('baseline-detail/', BaselineDetailView.as_view(), name='baseline-detail'),
    path('baseline/', BaselineAnalyticsView.as_view(), name='baseline-analytics'),
    path('requests/', RequestsAnalyticsView.as_view(), name='requests-analytics'),
    path('tracking/', TrackingAnalyticsView.as_view(), name='tracking-analytics'),

    # User Dashboard
    
    #Common dashboard (client admin & portal admin)
    path("ba/usage-summary/", BAUsageSummaryView.as_view(), name="ba-usage-summary"),
    path("ba/optimization-summary/", BAOptimizationSummaryView.as_view(), name="ba-optimization-summary"),
    path("ba/top-savings/", BATopSavingsView.as_view(), name="ba-top-savings"),
    path("ba/savings-timeseries/", BASavingsTimeSeriesView.as_view(), name="ba-savings-timeseries"),
    path('bill-summary/', BillSummaryView.as_view(), name='bill-summary'),
    path('bill-extremes/', BillExtremesView.as_view(), name='bill-extremes'),
    path('bill-totals/', BillTotalsView.as_view(), name='bill-totals'),
    path('bill-status-breakdown/', BillStatusBreakdownView.as_view(), name='bill-status-breakdown'),
    path('bill-timeseries/', BillTimeSeriesView.as_view(), name='bill-timeseries'),
    path("request-summary/", RequestSummaryView.as_view(), name="request-summary"),
    #Common dashboard (client admin & portal admin)

    
    path('', AnalysisView.as_view(), name='analysis-list-create'),
    path('multiple/', MultipleUploadView.as_view(), name='multiple-analysis-list-create'),
    path('analysis-dashboard/', AnalysisDashboardView.as_view(), name='analysis-dashboard'),
    path('analysis-lines/', AnalysisLinesView.as_view(), name='analysis-lines'),
    path('bot/<str:ChatType>/<int:pk>/', AnalysisBotView.as_view(), name='analysis-bot'),
    path('<str:pk>/', AnalysisView.as_view(), name='analysis-detail'),
    path('multiple/<str:pk>/', MultipleUploadView.as_view(), name='multiple-analysis-detail'),
    path('<int:pk>/download-xlsx/', download_analysis_xlsx_file.as_view(), name='download-analysis-xlsx'),
    path('get-chat-pdf/<str:pk>/', GetChatPdfView.as_view(), name='get-chat-pdf'),
    path('get-savings-pdf/<str:pk>/', GetSavingsPdfView.as_view(), name='get-savings-pdf'),
    
    path('analysis-dashboard/', AnalysisDashboardView.as_view(), name='analysis-dashboard'),
    path('analysis-lines/', AnalysisLinesView.as_view(), name='analysis-lines'),
]



# urlpatterns = [
#     path('', AnalysisView.as_view(), name='analysis-list-create'),
#     path('multiple/', MultipleUploadView.as_view(), name='multiple-analysis-list-create'),
    

#     path('bot/<str:ChatType>/<int:pk>/', AnalysisBotView.as_view(), name='analysis-bot'),
#     path('<str:pk>/', AnalysisView.as_view(), name='analysis-detail'),
#     path('multiple/<str:pk>/', MultipleUploadView.as_view(), name='multiple-analysis-detail'),
#     path('<str:pk>/download-xlsx/', download_analysis_xlsx_file.as_view(), name='download-analysis-xlsx'),
#     path('get-chat-pdf/<str:pk>/', GetChatPdfView.as_view(), name='get-chat-pdf'),
#     path('get-savings-pdf/<str:pk>/', GetSavingsPdfView.as_view(), name='get-savings-pdf'),
# ]
