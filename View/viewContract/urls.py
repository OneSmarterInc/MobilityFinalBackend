from django.urls import path
from .views import viewContractView

viewcontract_urls = [
    path('view-contract/', viewContractView.as_view(), name='view-contract-list-create'),
    path('view-contract/<int:pk>/', viewContractView.as_view(), name='view-contract-detail'),
    
]