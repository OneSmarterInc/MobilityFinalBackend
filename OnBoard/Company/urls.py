from django.urls import path
from .views import CompanyView

companyurls = [
    path("company/", CompanyView().as_view(), name='company-list-create'),
    path("company/<str:pk>/", CompanyView().as_view(), name='company-detail'),
]
