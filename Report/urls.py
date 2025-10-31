from django.urls import path
from .Payment.urls import paymenturls
urlpatterns = [

]
# urlpatterns = [
#     path('view-report1/', ViewReportView.as_view(), name='view-report-detail'),
#     path('view-report1/<report_type>/', ViewReportView.as_view(), name='view-report-detail'),
#     path('view-report1/<report_type>/<sub_type>/', ViewReportView.as_view(), name='view-report-detail'),
#     path('view-report1/<pk>/', ViewReportView.as_view(), name='view-report-delete-update'),

#     path('upload-report1/', UploadFileView.as_view(), name='upload-file-detail'),
#     path('upload-report1/<report_type>/', UploadFileView.as_view(), name='upload-file-report-detail'),
#     path('upload-report1/<report_type>/<pk>/', UploadFileView.as_view(), name='upload-file-delete-update'),
# ]
urlpatterns.extend(paymenturls)


from .Views.uploadbilled import UploadBilledReportView
from .Views.uploadunbilled import UploadUnbilledReportView
from .Views.viewbilled import ViewBilledReportView
from .Views.viewunbilled import ViewUnbilledReportView
from .views import GetReportDataView
# from .Views.viewunbilled import ViewUnbilledReportView
newurlspatterns = [



    # View Report URLs
    # path('view-report/unbilled/<sub_type>/'),
    path('view-report/billed/', view=ViewBilledReportView.as_view(), name='view-billed-report-detail'),
    path('view-report/billed/<sub_type>/', view=ViewBilledReportView.as_view(), name='view-billed-report-detail'),
    path('view-report/unbilled/', view=ViewUnbilledReportView.as_view(), name='view-unbilled-report-detail'),
    path('view-report/unbilled/<sub_type>/', view=ViewUnbilledReportView.as_view(), name='view-unbilled-report-detail'),

    # path('view-report/unbilled/<pk>/'),
    # path('view-report/billed/<pk>/'),


    # Upload Report URLs
    path('upload-report/unbilled/', view=UploadUnbilledReportView.as_view(), name='upload-unbilled-report'),
    path('upload-report/billed/', view=UploadBilledReportView.as_view(), name='upload-billed-report'),
    path('upload-report/unbilled/<pk>/', view=UploadUnbilledReportView.as_view(), name='upload-unbilled-report-detail-delete'),
    
    path('upload-report/billed/<pk>/', view=UploadBilledReportView.as_view(), name='upload-billed-report-detail-delete'),
    path('get-report-initials/', view=GetReportDataView.as_view(), name='get-report-data'),
]
urlpatterns.extend(newurlspatterns)
from .OtherReports import *

other_report_urls = [
    path('asset-tracking', Get_Asset_Tracking_asset_master_report.as_view(), name='get_asset_tracking_report'),
   path('downalod_asset-tracking', Download_Asset_Tracking_asset_master_report.as_view(), name='download_asset_tracking_report'), 
   path('asset-transactions', Get_Asset_Transactions.as_view(), name='get_asset_transactions'),
   path('downalod_asset-transactions', Download_Asset_Transactions.as_view(), name='download_asset_transactions'),
   path('outstanding-loaners', Get_Outstanding_Loaners_report.as_view(), name='get_outstanding_loaners_report'),
   path('downalod_outstanding-loaners', Download_Outstanding_Loaners_report.as_view(), name='download_outstanding_loaners_report'),
   path('order-tracking', Get_Order_Tracking_report.as_view(), name='get_order_tracking_report'),
   path('downalod_order-tracking', Download_Order_Tracking_report.as_view(), name='download_order_tracking_report'),
   path('contact', Get_Contact_report.as_view(), name='get_contact_report'),
   path('downalod_contact', Download_Contact_report.as_view(), name='download_contact_report'),
   path('ban-autopay', Get_BAN_Autopay_Enabled_Listing_report.as_view(), name='get_ban_autopay_report'),
   path('downalod_ban-autopay', Download_BAN_Autopay_Enabled_Listing_report.as_view(), name='download_ban_autopay_report'),
   path('phone-numbers', Get_Phone_Numbers_List_By_Organization_report.as_view(), name='get_phone_numbers_report'),
   path('downalod_phone-numbers', Download_Phone_Numbers_List_By_Organization_report.as_view(), name='download_phone_numbers_report'),
   path("approve_all",Approve_all_data.as_view()),



# -------------------------------------------Reports by Kunal---------------------------------------------------------


   path('vendor-summary-report/', get_vendor_summary_report, name='vendor_summary_report'),
   path('vendor_summary_report_download/', vendor_summary_report_download, name='vendor_summary_report_download'),

    path('division_summary_report/', division_summary_report, name='division_summary_report'),
    path('division_summary_report_download/', division_summary_report_download, name='division_summary_report_download'),

    path('get_vendors_by_organization/', get_vendors_by_organization, name='get_vendors_by_organization'),
    path('get_bans_by_organization_vendor/', get_bans_by_organization_vendor, name='get_bans_by_organization_vendor'),
    path('get_entrytype_bans_by_organization/', get_entrytype_bans_by_organization, name='get_entrytype_bans_by_organization'),
    path('get-division/', GetDivisionView.as_view(), name='get_division'),
    path('get-location/', GetLocationView.as_view(), name='get_location'),

    path('un_orapprovedbills_base_tem_report/', un_orapprovedbills_base_tem_report, name='approvedbills_base_tem_report'),
    path('approved_bills_base_tem_report_download/', approved_bills_base_tem_report_download, name='approved_bills_base_tem_report_download'),

    path('get_sub_company_by_company',GetSubCompanyByCompany.as_view()),

    path('un_orapprovedbills_consoliated_tem_report/', un_or_approvedbills_consoliated_tem_report, name='approvedbills_consoliated_tem_report'),
    path('approved_bills_consoliated_tem_report_download/', approved_bills_consoliated_tem_report_download, name='approved_bills_consoliated_tem_report_download'),

    path('unapprovedbills_base_tem_report/', unapprovedbills_base_tem_report, name='unapprovedbills_base_tem_report'),
    path('unapproved_bills_base_tem_report_download/', unapproved_bills_base_tem_report_download, name='unapproved_bills_base_tem_report_download'),

    path('unapprovedbills_consoliated_tem_report/', unapprovedbills_consoliated_tem_report, name='unapprovedbills_consoliated_tem_report'),
    path('unapproved_bills_consoliated_tem_report_download/', unapproved_bills_consoliated_tem_report_download, name='unapproved_bills_consoliated_tem_report_download'),

   path('highest_expense_bills_report/', highest_expense_bills_report, name='highest_expense_bills_report'),
   path('highest_expense_bills_report_download/', highest_expense_bills_report_download, name='highest_expense_bills_report_download'),


   path('location_level_bill_summary_report/', location_level_bill_summary_report, name='location_level_bill_summary_report'),
   path('location_level_bill_summary_report_download/', location_level_bill_summary_report_download, name='location_level_bill_summary_report_download'),

   path('location_level_service_summary_report/', location_level_service_summary_report, name='location_level_service_summary_report'),
   path('location_level_service_summary_report_download/', location_level_service_summary_report_download, name='location_level_service_summary_report_download'),


   path('baseline_billing_report/', baseline_billing_report, name='baseline_billing_report'),
   path('baseline_billing_report_download/', baseline_billing_report_download, name='baseline_billing_report_download'),

   path('invoice_tracking_report/', invoice_tracking_report, name='invoice_tracking_report'),
   path('invoice_tracking_report_download/', invoice_tracking_report_download, name='invoice_tracking_report_download'),


   path('out_of_variance_report/', out_of_variance_report, name='out_of_variance_report'),
   path('out_of_variance_report_download/', out_of_variance_report_download, name='out_of_variance_report_download'),

   path('missing_bills_base_tem_report/', missing_bills_base_tem_report, name='missing_bills_base_tem_report'),
   path('missing_bills_base_tem_report_download/', missing_bills_base_tem_report_download, name='missing_bills_base_tem_report_download'),

   path('missing_bills_consoliated_tem_report/', missing_bills_consoliated_tem_report, name='missing_bills_consoliated_tem_report'),
   path('missing_bills_consoliated_tem_report_download/', missing_bills_consoliated_tem_report_download, name='missing_bills_consoliated_tem_report_download'),

   path('cost_center_summary_report/', cost_center_summary_report, name='cost_center_summary_report'),
   path('cost_center_summary_report_download/', cost_center_summary_report_download, name='cost_center_summary_report_download'),

   path('cost_center_detailed_report/', cost_center_detailed_report, name='cost_center_detailed_report'),
   path('cost_center_detailed_report_download/', cost_center_detailed_report_download, name='cost_center_detailed_report_download'),

   path('location_summary_report/', location_summary_report, name='location_summary_report'),
   path('location_summary_report_download/', location_summary_report_download, name='location_summary_report_download'),

   path('duplicate_bills_base_tem_report/', duplicate_bills_base_tem_report, name='duplicate_bills_base_tem_report'),
   path('duplicate_bills_base_tem_report_download/', duplicate_bills_base_tem_report_download, name='duplicate_bills_base_tem_report_download'),

   path('service_by_type_report/', service_by_type_report, name='service_by_type_report'),
   path('service_by_type_report_download/', service_by_type_report_download, name='service_by_type_report_download'),

   path('payment_detail_report/', payment_detail_report, name='payment_detail_report'),
   path('payment_detail_report_download/', payment_detail_report_download, name='payment_detail_report_download'),

   path('mobile_unapproved_bills_report/', mobile_unapproved_bills_report, name='mobile_unapproved_bills_report'),
   path('mobile_unapproved_bills_report_download/', mobile_unapproved_bills_report_download, name='mobile_unapproved_bills_report_download'),

   path('entered_bills_report/', entered_bills_report, name='entered_bills_report'),
   path('entered_bills_report_download/', entered_bills_report_download, name='entered_bills_report_download'),

   path('organization_location_listing_report/', organization_location_listing_report, name='organization_location_listing_report'),
   path('organization_location_listing_report_download/', organization_location_listing_report_download, name='organization_location_listing_report_download'),

   path('organization_location_report/', organization_location_report, name='organization_location_report'),
   path('organization_location_report_download/', organization_location_report_download, name='organization_location_report_download'),

   path('inactive_location_report/', inactive_location_report, name='inactive_location_report'),
   path('inactive_location_report_download/', inactive_location_report_download, name='inactive_location_report_download'),

   path('location_filter_report/', location_filter_report, name='location_filter_report'),
   
   path('organization_ban_listing_by_location/', organization_ban_listing_by_location, name='organization_ban_listing_by_location'),
   path('organization_ban_listing_by_location_download/', organization_ban_listing_by_location_download, name='organization_ban_listing_by_location_download'),


   path('organization_ban_listing_by_vendor/', organization_ban_listing_by_vendor, name='organization_ban_listing_by_vendor'),
   path('organization_ban_listing_by_vendor_download/', organization_ban_listing_by_vendor_download, name='organization_ban_listing_by_vendor_download'),

   path('organization_cost_centers_by_account/', organization_cost_centers_by_account, name='organization_cost_centers_by_account'),
   path('organization_cost_centers_by_account_download/', organization_cost_centers_by_account_download, name='organization_cost_centers_by_account_download'),

   path('inventory_report/', inventory_report, name='inventory_report'),
   path('inventory_report_download/', inventory_report_download, name='inventory_report_download'),

   path('circuit_list_by_organization/', circuit_list_by_organization, name='circuit_list_by_organization'),
   path('circuit_list_by_organization_download/', circuit_list_by_organization_download, name='circuit_list_by_organization_download'),

   path('circuit_list_by_organization_contracts/', circuit_list_by_organization_contracts, name='circuit_list_by_organization_contracts'),
   path('circuit_list_by_organization_contracts_download/', circuit_list_by_organization_contracts_download, name='circuit_list_by_organization_contracts_download'),

   path('carrier_pic_report/', carrier_pic_report, name='carrier_pic_report'),
   path('carrier_pic_report_download/', carrier_pic_report_download, name='carrier_pic_report_download'),

   path('inactive_accounts_report/', inactive_accounts_report, name='inactive_accounts_report'),
   path('inactive_accounts_report_download/', inactive_accounts_report_download, name='inactive_accounts_report_download'),

]

urlpatterns.extend(other_report_urls)
from .ReportsByGRD import (
    get_vendor_summary_report,
    get_base_bills_report,
    get_division_summary_report,
    get_consolidated_bills_report,
    get_highest_expense_report,
    get_baseline_billing_report,
    get_location_level_service_summary_report,
    get_location_level_bill_summary_report,
    get_invoice_tracking_report,
    get_cost_center_detailed_report,
    get_cost_center_summary_report,
    get_missing_bills_base_tem_report,
    get_missing_bills_consolidated_tem_report,
    get_out_of_variance_report,
    get_location_summary_report,
    get_duplicate_bills_base_tem_report,
    get_payment_detail_report,
    get_service_by_type_report,
    get_organization_location_listing_report,
    get_mobile_bills_report,
    get_entered_bills_report,
    get_filter_location_report,
    get_Inactive_location_report,
    get_organization_location_report,
    get_asset_tracking_report,
    get_asset_transactions_report,
    get_ban_autopay_listing_report,
    get_ban_by_location_report,
    get_ban_by_vendor_report,
    get_contact_report,
    get_Inactive_bans_report,
    get_order_tracking_report,
    get_outstanding_loaners_report,
    get_phone_list_byOrg_report,
    get_inventory_report
)


my_report_urls = [
    path("other-reports/vendor-summary-report/", view=get_vendor_summary_report, name="vendor_summary_report"),
    path("other-reports/division-summary-report/", view=get_division_summary_report, name="division_summary_report"),
    path("other-reports/base-bills-report/", view=get_base_bills_report, name="get_base_bills_report"),
    path("other-reports/consolidated-bills-report/", view=get_consolidated_bills_report, name="consolidated_bills_report"),
    path("other-reports/highest-expense-report/", view=get_highest_expense_report, name="highest_expense_report"),
    path("other-reports/baseline-billing-report/", view=get_baseline_billing_report, name="baseline_billing_report"),
    path("other-reports/location-level-service-summary-report/", view=get_location_level_service_summary_report, name="location_level_service_summary_report"),
    path("other-reports/location-level-bill-summary-report/", view=get_location_level_bill_summary_report, name="location_level_bill_summary_report"),
    path("other-reports/invoice-tracking-report/", view=get_invoice_tracking_report, name="invoice_tracking_report"),
    path("other-reports/cost-center-detailed-report/", view=get_cost_center_detailed_report, name="cost_center_detailed_report"),
    path("other-reports/cost-center-summary-report/", view=get_cost_center_summary_report, name="cost_center_summary_report"),
    path("other-reports/missing-bills-base-tem-report/", view=get_missing_bills_base_tem_report, name="missing_bills_base_tem_report"),
    path("other-reports/missing-bills-consolidated-tem-report/", view=get_missing_bills_consolidated_tem_report, name="missing_bills_consolidated_tem_report"),
    path("other-reports/out-of-variance-report/", view=get_out_of_variance_report, name="out_of_variance_report"),
    path("other-reports/location-summary-report/", view=get_location_summary_report, name="location_summary_report"),
    path("other-reports/duplicate-bills-base-tem-report/", view=get_duplicate_bills_base_tem_report, name="duplicate_bills_base_tem_report"),
    path("other-reports/payment-detail-report/", view=get_payment_detail_report, name="payment_detail_report"),
    path("other-reports/service-by-type-report/", view=get_service_by_type_report, name="service_by_type_report"),
    path("other-reports/organization-location-listing-report/", view=get_organization_location_listing_report, name="organization_location_listing_report"),
    path("other-reports/filter-location-report/", view=get_filter_location_report, name="filter_location_report"),
    path("other-reports/inactive-location-report/", view=get_Inactive_location_report, name="inactive_location_report"),
    path("other-reports/organization-location-report/", view=get_organization_location_report, name="organization_location_report"),
    path("other-reports/asset-tracking-report/", view=get_asset_tracking_report, name="asset_tracking_report"),
    path("other-reports/asset-transactions-report/", view=get_asset_transactions_report, name="asset_transactions_report"),
    path("other-reports/ban-autopay-listing-report/", view=get_ban_autopay_listing_report, name="ban_autopay_listing_report"),
    path("other-reports/ban-by-location-report/", view=get_ban_by_location_report, name="ban_by_location_report"),
    path("other-reports/ban-by-vendor-report/", view=get_ban_by_vendor_report, name="ban_by_vendor_report"),
    path("other-reports/contact-report/", view=get_contact_report, name="contact_report"),
    path("other-reports/inactive-bans-report/", view=get_Inactive_bans_report, name="inactive_bans_report"),
    path("other-reports/order-tracking-report/", view=get_order_tracking_report, name="order_tracking_report"),
    path("other-reports/outstanding-loaners-report/", view=get_outstanding_loaners_report, name="outstanding_loaners_report"),
    path("other-reports/phone-list-byorg-report/", view=get_phone_list_byOrg_report, name="phone_list_byorg_report"),
    path("other-reports/mobile-bills-report/", view=get_mobile_bills_report, name="mobile_bills_report"),
    path("other-reports/entered-bills-report/", view=get_entered_bills_report, name="entered_bills_report"),
    path("other-reports/inventory_report/", view=get_inventory_report, name="inventory_report"),
]

urlpatterns.extend(my_report_urls)