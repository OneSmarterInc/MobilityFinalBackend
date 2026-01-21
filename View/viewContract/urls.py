from django.urls import path
from .views import viewContractView

viewcontract_urls = [
    path('view-contract/', viewContractView.as_view(), name='view-contract-create'),
    path('view-contract-fetch/<int:org>/', viewContractView.as_view(), name='view-contract-list'),
    path('view-contract/<int:pk>/', viewContractView.as_view(), name='view-contract-detail'),
    
]