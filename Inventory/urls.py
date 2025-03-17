from django.urls import path
from .views import InventorySubjectView, InventoryDataView, BanInfoView, UploadConsolidated, Mobiles

urlpatterns = [
    path('filter-inventory-subjects/', InventorySubjectView.as_view(), name='get-post'),
    path('filter-inventory-data/<subject>/', InventoryDataView.as_view(), name='get-data'),
    path('filter-inventory-data/<subject>/<id>/', InventoryDataView.as_view(), name='delete-data'),
    path('ban-info/<org>/<vendor>/<ban>/', BanInfoView.as_view(), name='ban-info'),
    path('upload-consolidated/', UploadConsolidated.as_view(), name='upload-consolidated'),
    path('mobiles/<account>/', Mobiles.as_view(), name='mobiles'),
]