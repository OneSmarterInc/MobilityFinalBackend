from django.urls import path
from .views import LocationView
from .views import LocationBulkUpload

locationurls = [
    path('location/', LocationView.as_view(), name='all-location-list-create'),
    path('<str:org>/location/', LocationView.as_view(), name='location-list-create'),
    path('<str:org>/location/<str:pk>/', LocationView.as_view(), name='location-detail')

]

bulkuploadurl = [
    path('<str:org>/location-bulk-upload/', LocationBulkUpload.as_view(), name='location-detail'),

]
locationurls.extend(bulkuploadurl)
