from .views import OnboardOrganizationView, LinksView, DivisionView, ChangeOrgStatus,AddVendortoOrg
from django.urls import path
orgurls = [
    path("organizations/", OnboardOrganizationView().as_view(), name='create-list-create'),
    path("organizations/<str:pk>/", OnboardOrganizationView().as_view(), name='create-detail'),
    path("organizations/<str:pk>/change-status/", ChangeOrgStatus, name='create-status'),

    path("organizations/<str:org>/divisions/", DivisionView().as_view(), name='division-list-create'),
    path("organizations/<str:org>/divisions/<str:pk>/", DivisionView().as_view(), name='division-detail'),

    path("organizations/<str:org>/links/", LinksView().as_view(), name='links-list-create'),
    path("organizations/<str:org>/links/<str:pk>/", LinksView().as_view(), name='links-detail'),
    path("organizations/add-vendor/<int:org>/", AddVendortoOrg().as_view(), name='add-org-vendor')
]
