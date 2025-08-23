from django.urls import path
from .views import InventorySubjectView, InventoryDataView, BanInfoView, UploadConsolidated, MobileView, OnboardedBaselineView, Homepageview,GetCompanyView

urlpatterns = [
    path('filter-inventory-subjects/', InventorySubjectView.as_view(), name='get-post'),
    path('filter-inventory-data/<subject>/', InventoryDataView.as_view(), name='get-data'),
    path('filter-inventory-data/<subject>/<id>/', InventoryDataView.as_view(), name='delete-data'),
    path('ban-info/<org>/<vendor>/<ban>/', BanInfoView.as_view(), name='ban-info'),
    path('upload-consolidated/', UploadConsolidated.as_view(), name='upload-consolidated'),
    path('mobiles/<account_number>/', MobileView.as_view(), name='mobiles-info-get'),
    path('mobiles/<account_number>/<wireless_number>/', MobileView.as_view(), name='mobiles-put-delete'),
    path('onboarded-baseline/<org>/<vendor>/<ban>/', OnboardedBaselineView.as_view(), name='onboarded-baseline'),
    path('home/<str:company>/', Homepageview.as_view(), name='home-page'),
    path('get-companies/', GetCompanyView.as_view(), name='company-view'),

]