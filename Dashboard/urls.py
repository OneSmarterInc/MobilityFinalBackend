from django.urls import path


urlpatterns = []

# vendors urls
from .CRUDViews.Admin.vendors import VendorView
vendorsurls = [
    
    path("vendors/", VendorView().as_view(), name='vendor-list-create'),
    path("vendors/<str:pk>/", VendorView().as_view(), name='vendor-detail')
]
urlpatterns.extend(vendorsurls)


# payment-type urls
from .CRUDViews.Admin.PayType import PaymentTypeView
PaymentTypeurls = [
    path("paytype/", PaymentTypeView().as_view(), name='paymenttype-list-create'),
    path("paytype/<str:pk>/", PaymentTypeView().as_view(), name='paymenttype-detail')
]
urlpatterns.extend(PaymentTypeurls)


# Invoice Method urls
from .CRUDViews.Admin.InvoiceMthd import InvoiceMethodView
InvoiceMthdurls = [
    path("invoicemthd/", InvoiceMethodView().as_view(), name='invoicemthd-list-create'),
    path("invoicemthd/<str:pk>/", InvoiceMethodView().as_view(), name='invoicemthd-detail')
]
urlpatterns.extend(InvoiceMthdurls)


# Ban Type urls
from .CRUDViews.Admin.BanType import BanTypeView
BanTypeurls = [
    path("bantype/", BanTypeView().as_view(), name='bantype-list-create'),
    path("bantype/<str:pk>/", BanTypeView().as_view(), name='bantype-detail')
]
urlpatterns.extend(BanTypeurls)

# Ban Status urls
from .CRUDViews.Admin.BanStatus import BanStatusView
BanStatusurls = [
    path("banstatus/", BanStatusView().as_view(), name='banstatus-list-create'),
    path("banstatus/<str:pk>/", BanStatusView().as_view(), name='banstatus-detail')
]
urlpatterns.extend(BanStatusurls)


# Entry Type urls
from .CRUDViews.Admin.EntryType import EntryTypeView
EntryTypeurls = [
    path("entrytype/", EntryTypeView().as_view(), name='entrytype-list-create'),
    path("entrytype/<str:pk>/", EntryTypeView().as_view(), name='entrytype-detail')
]
urlpatterns.extend(EntryTypeurls)

# Cost Center Level urls
from .CRUDViews.Admin.CostCenterLvl import CostCenterLevelView
CostCenterLvlurls = [
    path("costcenterlvl/", CostCenterLevelView().as_view(), name='costcenterlvl-list-create'),
    path("costcenterlvl/<str:pk>/", CostCenterLevelView().as_view(), name='costcenterlvl-detail')
]
urlpatterns.extend(CostCenterLvlurls)


# Cost Center Type urls
from .CRUDViews.Admin.CostCenterTyp import CostCenterTypeView
CostCenterTypurls = [
    path("costcentertype/", CostCenterTypeView().as_view(), name='costcentertype-list-create'),
    path("costcentertype/<str:pk>/", CostCenterTypeView().as_view(), name='costcentertype-detail')
]
urlpatterns.extend(CostCenterTypurls)


# permissions urls
from .CRUDViews.Admin.Permissions import PermissionView
Permissionurls = [
    path("permissions/", PermissionView().as_view(), name='permissions-list-create'),
    path("permissions/<str:pk>/", PermissionView().as_view(), name='permission-detail'),
]
urlpatterns.extend(Permissionurls)


# User Roles urls
from .CRUDViews.Admin.Roles import UserRoleView
useroles = [
    path("useroles/", UserRoleView().as_view(), name='useroles-list-create'),
    path("useroles/<str:pk>/", UserRoleView().as_view(), name='user-role-detail'),
]
urlpatterns.extend(useroles)


# location urls
from .CRUDViews.Admin.loc import LocView
loc = [
    path("loc/", LocView().as_view(), name='loc-list-create'),
    path("loc/<str:pk>/", LocView().as_view(), name='loc-detail'),
]
urlpatterns.extend(loc)

# company urls
from .CRUDViews.Admin.com import CompanyView
company = [
    path("company/", CompanyView().as_view(), name='company-list-create'),
    path("company/<str:pk>/", CompanyView().as_view(), name='company-detail'),
]
urlpatterns.extend(company)

# billtype urls

from .CRUDViews.Admin.billtype import BillTypeView
billtype = [
    path("billtype/", BillTypeView().as_view(), name='billtype-list-create'),
    path("billtype/<str:pk>/", BillTypeView().as_view(), name='billtype-detail'),
]
urlpatterns.extend(billtype)
 

from .CRUDViews.Manageusers import ManageUsersView
manageusers = [
    path("manage-users/", ManageUsersView().as_view(), name='manageusers-list-create'),
    path("manage-users/<pk>/", ManageUsersView().as_view(), name='manageusers-detail'),
]
urlpatterns.extend(manageusers)

from .CRUDViews.Profilemanagement import ProfileManageView, ProfilePermissionsView,GetUserbyOrgView,ProfileUpdateView
profilemanagement = [
    path("profile-management/", ProfileManageView().as_view(), name='profilemanagement-list-create'),
    path("profile-management/<pk>/", ProfileManageView().as_view(), name='profilemanagement-detail'),
    path("get-user-by-org/<org>/", GetUserbyOrgView().as_view(), name='get-by-org'),
    path("update-profile/<pk>/", ProfileUpdateView().as_view(), name='update-profile'),
]
profilepermissions = [
    path("profile-permissions/", ProfilePermissionsView().as_view(), name='profilepermission-list-create'),
    path("profile-permissions/<pk>/", ProfilePermissionsView().as_view(), name='profilepermission-detail'),
]
urlpatterns.extend(profilemanagement)
urlpatterns.extend(profilepermissions)

from .CRUDViews.Inventory import InventoryView, MovebanView
inventory = [
    path("inventory/<org>/", InventoryView().as_view(), name='inventory-list-create'),
    path("inventory/<org>/<pk>/", InventoryView().as_view(), name='inventory-detail'),
    path("move-ban/<pk>/", MovebanView().as_view(), name='move-ban'),
]
urlpatterns.extend(inventory)

from .CRUDViews.Inventory import AddNewInventoryView, DownloadInventoryExcel

addnew = [
    path("add-new-inventory/<org>/", AddNewInventoryView().as_view(), name='new-inventory-list-create'),
]
urlpatterns.extend(addnew)

downloadexcel = [
    path("download-inventory-excel/<org>/", DownloadInventoryExcel().as_view(), name='download-excel'),
]
urlpatterns.extend(downloadexcel)
from .CRUDViews.vendors import VendorsView
vendors = [
    path("vendors-portal/", VendorsView().as_view(), name='vendorportal-list-create'),
    path("vendors-portal/<pk>/", VendorsView().as_view(), name='vendorportal-detail'),
]
urlpatterns.extend(vendors)

from .CRUDViews.catManagement import CategoryView
catgories = [
    path("categories/", CategoryView().as_view(), name='Category-list-create'),
    path("categories/<pk>/", CategoryView().as_view(), name='Category-detail'),
]
urlpatterns.extend(catgories)

from .CRUDViews.changepassword import ChangePassswordView
change = [
    path("change-password/", ChangePassswordView().as_view(), name='change-list-create'),
    path("change-password/<pk>/", ChangePassswordView().as_view(), name='change-detail'),
]
urlpatterns.extend(change)

from .CRUDViews.requests import RequestsView, OnlineFormView, RequestLogsView, RequestExcelUploadView, UniqueLineView, RequestUsersExcelUploadView
from .CRUDViews.employeeRaiseRequest import EmployeeRequest, DeviceUpgradeView

requests = [
    path("requests-management/", RequestsView().as_view(), name='requests-list-create'),
    path("requests-management/<pk>/", RequestsView().as_view(), name='requests-detail'),
    path("unique-line/<phone>/",UniqueLineView.as_view(),name='unique'),
    path("request-users-excel-upload/<org>/",RequestUsersExcelUploadView.as_view(), name='request-users-excel'),
    path("employee-request/<email>/",EmployeeRequest.as_view(), name='employee-request'),
    # path("upgrade-device-request/<email>/",DeviceUpgradeView.as_view(), name='upgrade-device-request'),
    path("upgrade-device-request/",DeviceUpgradeView.as_view(), name='get-upgrade-device-request'),
    path("upgrade-device-request/<pk>/",DeviceUpgradeView.as_view(), name='get-upgrade-device-request'),
]

urlpatterns.extend(requests)

requestsform = [
    path("request-management/requests-form/", OnlineFormView().as_view(), name='form-create'),
    path("request-management/excel-upload/<org>/", RequestExcelUploadView().as_view(), name='form-create'),
]
urlpatterns.extend(requestsform)

requestslogs = [
    path("request-management/request-logs/", RequestLogsView().as_view(), name='request-logs-detail'),
    # path("requests-management/<pk>/request-logs/", RequestLogsView().as_view(), name='request-logs-detail'),
]
urlpatterns.extend(requestslogs)

from .CRUDViews.devices import DevicesView

devicesurl = [
    path("devices/",view=DevicesView.as_view(), name='devices'),
    path("devices/<int:pk>/",view=DevicesView.as_view(),name='devices-update')
]
urlpatterns.extend(devicesurl)

from .CRUDViews.makemodels import MakeModelView

devicemodelsurl = [
    path("device-models/",view=MakeModelView.as_view(), name='device-models'),
    path("device-models/<int:pk>/",view=MakeModelView.as_view(),name='device-models-update')
]
urlpatterns.extend(devicemodelsurl)

from .CRUDViews.vendor_devices import VendorDeviceView

vendordeviceurl = [
    path("vendor-device/",view=VendorDeviceView.as_view(), name='vendor-device-list'),
    path("vendor-device/<int:pk>/",view=VendorDeviceView.as_view(),name='vendor-device-update')
]
urlpatterns.extend(vendordeviceurl)

from .CRUDViews.vendor_information import VendorInformationView,getBansView,ReplacePlanView

vendorinfourl = [
    path("vendor-information/",view=VendorInformationView.as_view(), name='vendor-device-list'),
    path("vendor-information/<int:pk>/",view=VendorInformationView.as_view(),name='vendor-device-update'),
    path("vendor-information/get-bans/<org>/",view=getBansView.as_view(),name='vendor-get-bans'),
    path("vendor-information/replace-plan/<int:pk>/",view=ReplacePlanView.as_view(),name='replace-plan'),
]
urlpatterns.extend(vendorinfourl)

from .CRUDViews.costcenters import CostCentersView, BulkCostCenterUpload

costcenterurl = [
    path("cost-centers/<org>/",view=CostCentersView.as_view(), name='cost-centers'),
    path("cost-centers/<org>/<int:pk>/",view=CostCentersView.as_view(),name='cost-centers-update'),
    path("cost-centers/bulk-upload/<int:sub_company>/<int:vendor>/<ban>/",view=BulkCostCenterUpload.as_view(),name='cost-centers-bulk-upload')
]

urlpatterns.extend(costcenterurl)

from .CRUDViews.vendor_plan import VendorPlanView
vendorplanurl = [
    path("vendor-plan/", view=VendorPlanView.as_view(), name='vendor-plan-list-create'),
    path("vendor-plan/<int:pk>/", view=VendorPlanView.as_view(), name='vendor-plan-detail'),
]
urlpatterns.extend(vendorplanurl)

from .CRUDViews.requests import TrackingInfoView
trakingurls = [
    path("request-tracking/", view=TrackingInfoView.as_view(), name='request-tracking'),
    path("request-tracking/<int:pk>/", view=TrackingInfoView.as_view(), name='request-tracking-detail'),
]
urlpatterns.extend(trakingurls)

from .CRUDViews.chatbot import ChatBotView
chatboturls = [
    path("chatbot/", view=ChatBotView.as_view(), name='chatbot'),
]
urlpatterns.extend(chatboturls)

