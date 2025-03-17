from django.urls import path


banurlpatterns = []

from .views import UploadBANView

uploadbanurls = [
    path("upload-ban/", UploadBANView.as_view(), name='upload-ban-list-create'),
    path("upload-ban/<str:pk>/", UploadBANView.as_view(), name='upload-ban-detail'),
]

from .views import OnboardBanView


onboardbanurls = [
    path("onboard-ban/", OnboardBanView.as_view(), name='onboard-ban-list-create'),
    path("onboard-ban/<str:pk>/", OnboardBanView.as_view(), name='onboard-ban-detail'),
]

from .views import InventoryUploadView

inventoryuploadurls = [
    path("inventory-upload/", InventoryUploadView.as_view(), name='inventory-upload-list-create'),
    path("inventory-upload/<str:pk>/", InventoryUploadView.as_view(), name='inventory-upload-detail'),
]

banurlpatterns.extend(uploadbanurls)
banurlpatterns.extend(onboardbanurls)
banurlpatterns.extend(inventoryuploadurls)
