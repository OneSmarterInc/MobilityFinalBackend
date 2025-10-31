
from django.shortcuts import render, HttpResponse
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import pandas as pd
from rest_framework.decorators import api_view, permission_classes
from OnBoard.Ban.models import BaseDataTable, UniquePdfDataTable, BaselineDataTable
from OnBoard.Location.models import Location
from OnBoard.Organization.models import Organizations, Links, Division
from datetime import datetime, timedelta
from django.forms.models import model_to_dict
from django.db.models import Func, DateField, F, Q, Sum
from django.db.models.functions import Cast
from collections import defaultdict
import re
from authenticate.models import PortalUser
from .generateExcelReport import GenerateExcelReport


def parse_custom_date(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%b %d %Y").date()
    except:
        return None

def is_bool(item):
    return item in (True, "true", 1, "True")

def parse_amount(value):
    """Clean and convert string amounts like '$1,234.50' → 1234.50"""
    if not value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return float(
        str(value)
        .replace("$", "")
        .replace(",", "")
        .strip()
    )

def parse_bill_month_year(date_str):
    try:
        bill_date = datetime.strptime(date_str.strip(), "%b %d %Y")
    except ValueError:
        bill_date = datetime.strptime(date_str.strip(), "%B %d %Y")

    return bill_date.strftime("%Y-%m")
def filter_by_range(data, start, end):
    formatted_start = parse_custom_date(start) if start else None
    formatted_end = parse_custom_date(end) if end else None

    filtered_data = data.annotate(
        bill_date_parsed=Func(
        F('bill_date'),
        function='STRFTIME',
        template="DATE(STRFTIME('%%%%Y-%%%%m-%%%%d', %(expressions)s))",
        output_field=DateField(),
    )
    )

    if formatted_start:
        filtered_data = filtered_data.filter(bill_date_parsed__gte=formatted_start)
    if formatted_end:
        filtered_data = filtered_data.filter(bill_date_parsed__lte=formatted_end)

    return filtered_data
base_data_billed = BaseDataTable.objects.exclude(viewuploaded=None, viewpapered=None)
base_data_onboarded = BaseDataTable.objects.exclude(banUploaded=None, banOnboarded=None)
unique_data_billed = UniquePdfDataTable.objects.exclude(viewuploaded=None, viewpapered=None)
unique_data_onboarded = UniquePdfDataTable.objects.exclude(banUploaded=None, banOnboarded=None)
baseline_data_billed = BaselineDataTable.objects.exclude(viewuploaded=None, viewpapered=None)
baseline_data_onboarded = BaselineDataTable.objects.exclude(banUploaded=None, banOnboarded=None)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vendor_summary_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')


    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    response = [model_to_dict(item, fields=["id", "bill_date", "sub_company", "net_amount", "vendor"]) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Vendor Summary Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_division_summary_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
    division = data.get('division')

    divObj = Division.objects.filter(id=division).first() if division else None

    locObj = Location.objects.filter(division=divObj) if divObj else None

    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)
    print(filtered_data.values_list("location",flat=True))
    if locObj:
        filtered_data = filtered_data.filter(location__in=locObj.values_list("site_name",flat=True))
    elif divObj and not locObj:
        return Response({"data":[]}, status=status.HTTP_200_OK)
    else:
        filtered_data = filtered_data


    start_date = data.get('start_date')
    end_date = data.get('end_date')
    filtered_data = base_data_billed.filter(accountnumber__in=filtered_data.values_list("accountnumber",flat=True))

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    response = [model_to_dict(item, fields=["id", "bill_date", "sub_company", "net_amount", "vendor"]) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Division Summary Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_base_bills_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))

    company = data.get('company')
    sub_company = data.get('sub_company')
    vendor = data.get('vendor')
    ban = data.get('ban')
    approve_status = data.get('approval_status', True)

    if not sub_company:
        return Response({"message":"Sub Company is required!"}, status=status.HTTP_400_BAD_REQUEST)
    

    start_date = data.get('start_date')
    end_date = data.get('end_date')

    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)
    filtered_data = filtered_data.filter(vendor=vendor) if vendor else filtered_data
    filtered_data = filtered_data.filter(accountnumber=ban) if ban else filtered_data

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    filtered_data = filtered_data.filter(is_baseline_approved=approve_status) if approve_status else filtered_data


    response = [model_to_dict(item, fields=["accountnumber", "invoicenumber", "vendor", "location", "bill_date", "variance", "net_amount", "created_at", "bill_approved_date"]) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Base Bills Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consolidated_bills_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')

    approve_status = data.get('approval_status', True)

    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)
    filtered_data = filtered_data.filter(is_baseline_approved=approve_status) if approve_status else filtered_data

    response = [model_to_dict(item, fields=["accountnumber", "invoicenumber", "vendor", "location", "bill_date", "variance", "net_amount", "created_at", "bill_approved_date"]) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Consolidated Bills Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_highest_expense_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')


    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date).order_by("-net_amount")[:25]


    response = [model_to_dict(item, fields=["accountnumber", "invoicenumber", "vendor", "location", "bill_date", "variance", "net_amount", "bill_approved_date"]) for item in filtered_data]
   
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Highest Expense Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_baseline_billing_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')


    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)
    
    response = [model_to_dict(item, fields=["accountnumber", "invoicenumber", "vendor", "location", "bill_date", "variance", "net_amount", "bill_approved_date"]) for item in filtered_data]
    print(response)

    uploaded_ids = filtered_data.values_list("viewuploaded", flat=True).distinct()
    papered_ids = filtered_data.values_list("viewpapered", flat=True).distinct()

    baseline_filter = baseline_data_billed.filter(
        Q(viewuploaded__in=uploaded_ids) |
        Q(viewpapered__in=[p for p in papered_ids if p is not None])
    )
    
    

    grouped_sums = defaultdict(float)
    total_sum_of_all_bill_dates = 0.0

    for item in baseline_filter:
        if item.viewuploaded_id:
            group_key = f"uploaded_{item.viewuploaded_id}"
        elif item.viewpapered_id:
            group_key = f"papered_{item.viewpapered_id}"
        else:
            group_key = "unknown"


        raw_charge = getattr(item, "total_charges", 0)
        if raw_charge is None:
            charge = 0.0
        else:
            if isinstance(raw_charge, str):
                raw_charge = re.sub(r"[^\d.\-]", "", raw_charge) 
            try:
                charge = float(raw_charge)
            except ValueError:
                charge = 0.0

        grouped_sums[group_key] += charge
        total_sum_of_all_bill_dates += charge

    response.append({
        "grouped_summary": dict(grouped_sums),
        "total_sum_of_all_bill_dates": round(total_sum_of_all_bill_dates, 2)
    })


    if is_download:
        reportObj = GenerateExcelReport(report_name="Baseline Billing Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_location_level_bill_summary_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')
    location = data.get('location')



    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)
    filtered_data = filtered_data.filter(location=location)
    
    account_numbers = filtered_data.values_list("accountnumber", flat=True)
    print(account_numbers)
    filtered_data = base_data_billed.filter(accountnumber__in=account_numbers) 

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)


    response = []
    for item in filtered_data:
        data = model_to_dict(item, fields=["vendor", "accountnumber", "bill_date", "net_amount"])
        data["location"] = location  # Add the extra field after conversion
        response.append(data)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Location Level Bill Summary Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_location_level_service_summary_report(request):

    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    location = data.get('location')



    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)
    filtered_data = filtered_data.filter(location=location)
    
    account_numbers = filtered_data.values_list("accountnumber", flat=True)
    print(account_numbers)
    filtered_data = base_data_billed.filter(accountnumber__in=account_numbers) 


    response = []
    for item in filtered_data:
        data = model_to_dict(item, fields=["vendor", "accountnumber", "bill_date", "net_amount"])
        data["location"] = location  # Add the extra field after conversion
        response.append(data)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Location Level Summary Service Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invoice_tracking_report(request):


    data = request.GET
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')

    billing_day_start = data.get('billing_day_start')
    billing_day_end = data.get('billing_day_end')


    
    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)
    billing_day_start = int(billing_day_start)
    billing_day_end = int(billing_day_end)

    filtered_data = filtered_data.filter(BillingDate__gte=billing_day_start, BillingDate__lte=billing_day_end)
    
    account_numbers = filtered_data.values_list("accountnumber", flat=True)
    filtered_data = base_data_billed.filter(accountnumber__in=account_numbers) 

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    

    
    response = [model_to_dict(item, fields=["id","location", "BillingName","BillingAdd", "BillingState", "BillingZip", "BillingCity", "BillingCountry", "vendor", "accountnumber", "bill_date", "date_due","net_amount"]) for item in filtered_data]

    uploaded_ids = filtered_data.values_list("viewuploaded", flat=True).distinct()
    papered_ids = filtered_data.values_list("viewpapered", flat=True).distinct()

    baseline_filter = baseline_data_billed.filter(
        Q(viewuploaded__in=uploaded_ids) |
        Q(viewpapered__in=[p for p in papered_ids if p is not None])
    )
    
    grouped_sums = defaultdict(float)
    total_sum_of_all_bill_dates = 0.0

    for item in baseline_filter:
        if item.viewuploaded_id:
            group_key = f"uploaded_{item.viewuploaded_id}"
        elif item.viewpapered_id:
            group_key = f"papered_{item.viewpapered_id}"
        else:
            group_key = "unknown"


        raw_charge = getattr(item, "total_charges", 0)
        if raw_charge is None:
            charge = 0.0
        else:
            if isinstance(raw_charge, str):
                raw_charge = re.sub(r"[^\d.\-]", "", raw_charge) 
            try:
                charge = float(raw_charge)
            except ValueError:
                charge = 0.0

        grouped_sums[group_key] += charge
        total_sum_of_all_bill_dates += charge

    response.append({
        "grouped_summary": dict(grouped_sums),
        "total_sum_of_all_bill_dates": round(total_sum_of_all_bill_dates, 2)
    })

    print(response)

    if is_download:
        reportObj = GenerateExcelReport(report_name="Invoice Tracking Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cost_center_summary_report(request):

    data = request.GET
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')


    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    
    response = [model_to_dict(item, fields=["id", "CostCenter", "net_amount", "accountnumber", "bill_date", "vendor", "bill_approved_date"]) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Cost Center Summary Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cost_center_detailed_report(request):


    data = request.GET
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')



    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    
    response = [model_to_dict(item, fields=["id", "CostCenter", "net_amount", "accountnumber", "bill_date", "vendor", "bill_approved_date", "master_account"]) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Cost Center Detailed Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_out_of_variance_report(request):

    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company', "OneSmarter")

    start_date = data.get('start_date')
    end_date = data.get('end_date')



    
    filtered_data = base_data_billed.filter(company=company) if company else base_data_billed
    filtered_data = base_data_billed.filter(sub_company=sub_company) if sub_company else filtered_data
    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    
    response = [model_to_dict(item, fields=["id", "location", "BillingName","BillingAdd", "BillingState", "BillingZip", "BillingCity", "BillingCountry","venodr","accountnumber", "variance","net_amount"]) for item in filtered_data]
    uploaded_ids = filtered_data.values_list("viewuploaded", flat=True).distinct()
    papered_ids = filtered_data.values_list("viewpapered", flat=True).distinct()

    baseline_filter = baseline_data_billed.filter(
        Q(viewuploaded__in=uploaded_ids) |
        Q(viewpapered__in=[p for p in papered_ids if p is not None])
    )
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Out of Service Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_missing_bills_base_tem_report(request):

    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')


    custom_date = data.get('custom_date') # Expected format: 'YYYY-MM'
    duration = data.get('duration')




    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)
    account_numbers = filtered_data.values_list("accountnumber", flat=True)
    filtered_data = base_data_billed.filter(accountnumber__in=account_numbers) 

    today = datetime.today()
    if duration == 'Current month':
        filter_month_year = today.strftime("%Y-%m")
    elif duration == 'Previous month':
        previous_month = (today.replace(day=1) - timedelta(days=1))
        filter_month_year = previous_month.strftime("%Y-%m")
    elif duration == 'Previous three months':
        last_three_months = [
            (today.replace(day=1) - timedelta(days=30 * i)).strftime("%Y-%m")
            for i in range(3)
        ]
    elif duration == 'Custom' and custom_date:
        try:
            filter_month_year = custom_date
            print(filter_month_year)
        except ValueError:
            return Response({'message': 'Invalid custom date format'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'message': 'Invalid duration or custom_date'}, status=status.HTTP_400_BAD_REQUEST)

    # filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    new_filtered_data = []
    for item in filtered_data:
        if item.bill_date: 
            try:
                bill_month_year = parse_bill_month_year(item.bill_date)
                print(bill_month_year)
                if duration == 'Previous three months' and bill_month_year in last_three_months:
                    new_filtered_data.append(item)
                elif duration != 'Previous three months' and bill_month_year == filter_month_year:
                    new_filtered_data.append(item)
            except ValueError:
                continue
    response = [model_to_dict(item, fields=["id", "location", "BillingName","BillingAdd", "BillingState", "BillingZip", "BillingCity", "BillingCountry","venodr","accountnumber","bill_date","invoicemethod"]) for item in new_filtered_data]
    print(response)

    if is_download:
        reportObj = GenerateExcelReport(report_name="Missing Bills Base T.E.M Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_missing_bills_consolidated_tem_report(request):

    data = request.GET
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')


    custom_date = data.get('custom_date') # Expected format: 'YYYY-MM'
    duration = data.get('duration')



    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    today = datetime.today()
    if duration == 'Current month':
        filter_month_year = today.strftime("%Y-%m")
    elif duration == 'Previous month':
        previous_month = (today.replace(day=1) - timedelta(days=1))
        filter_month_year = previous_month.strftime("%Y-%m")
    elif duration == 'Previous three months':
        last_three_months = [
            (today.replace(day=1) - timedelta(days=30 * i)).strftime("%Y-%m")
            for i in range(3)
        ]
    elif duration == 'Custom' and custom_date:
        try:
            filter_month_year = custom_date
        except ValueError:
            return Response({'message': 'Invalid custom date format'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'message': 'Invalid duration or custom_date'}, status=status.HTTP_400_BAD_REQUEST)

    # filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    new_filtered_data = []
    for item in filtered_data:
        if item.bill_date: 
            try:
                bill_date = datetime.strptime(item.bill_date, "%B %d %Y")
                bill_month_year = bill_date.strftime("%Y-%m")

                if duration == 'Previous three months' and bill_month_year in last_three_months:
                    new_filtered_data.append(item)
                elif duration != 'Previous three months' and bill_month_year == filter_month_year:
                    new_filtered_data.append(item)
            except ValueError:
                continue
    response = [model_to_dict(item, fields=["id", "location", "BillingName","BillingAdd", "BillingState", "BillingZip", "BillingCity", "BillingCountry","venodr","accountnumber","bill_date","invoicemethod"]) for item in new_filtered_data]
    print(response)

    if is_download:
        reportObj = GenerateExcelReport(report_name="Missing Bills Consolidated T.E.M Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_location_summary_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')


    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    response = [model_to_dict(item, fields=["id", "bill_date", "sub_company", "net_amount", "vendor", "BillingName","BillingAdd", "BillingState", "BillingZip", "BillingCity", "BillingCountry"]) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Location Summary Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_duplicate_bills_base_tem_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    sub_company = data.get('sub_company')
    company = data.get('company')

    custom_date = request.GET.get('date')  # Expected format: 'YYYY-MM'


    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    if custom_date:
        matched_data = []

        for item in filtered_data:
            bill_date_str = item.bill_date
            if not bill_date_str:
                continue

            try:
                bill_month_year = parse_bill_month_year(bill_date_str)
                if bill_month_year == custom_date:
                    matched_data.append(item.id)
            except Exception:
                continue 

        filtered_data = base_data_billed.filter(id__in=matched_data)

    uploaded_ids = filtered_data.values_list("viewuploaded", flat=True).distinct()
    papered_ids = filtered_data.values_list("viewpapered", flat=True).distinct()

    baseline_filter = baseline_data_billed.filter(
        Q(viewuploaded__in=uploaded_ids) |
        Q(viewpapered__in=[p for p in papered_ids if p is not None])
    )
    charges_summary = (
        baseline_filter
        .values("viewuploaded", "viewpapered")
        .annotate(total_charges_sum=Sum("total_charges"))
    )
    print(charges_summary)
    charges_lookup = {}
    for item in charges_summary:
        key = (item["viewuploaded"], item["viewpapered"])
        charges_lookup[key] = item["total_charges_sum"]

    response = []
    for item in filtered_data:
        data = model_to_dict(item, exclude=["summary_file","batch_file"])
        key = (item.viewuploaded, item.viewpapered)
        data["total_charges_sum"] = charges_lookup.get(key, 0)  # default 0 if not found
        response.append(data)

    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Duplicate Bills Base T.E.M Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_service_by_type_report(request):


    data = request.GET
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')



    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    # reverse by net amount
    filtered_data = filtered_data.order_by("-net_amount")
    
    response = [model_to_dict(item, exclude=["summary_file", "batch_file"]) for item in filtered_data]

    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Service by type Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_detail_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')
    vendor = data.get('vendor')
    ban = data.get('ban')

    start_date = data.get('start_date')
    end_date = data.get('end_date')
    invoice_type = request.GET.get('invoice_type')




    
    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)
    filtered_data = base_data_onboarded.filter(vendor=vendor) if vendor else filtered_data
    
    filtered_data = base_data_onboarded.filter(accountnumber=ban) if ban else filtered_data
    account_numbers = filtered_data.values_list("accountnumber", flat=True)
    filtered_data = base_data_billed.filter(accountnumber__in=account_numbers) 

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    filtered_data = filtered_data.filter(invoicemethod=invoice_type) if invoice_type else filtered_data

    
    response = [model_to_dict(item, fields=["id", "vendor", "accountnumber", "invoicenumber", "bill_approved_date", "bill_date", "date_due"]) for item in filtered_data]

    print("filtered==", filtered_data)

    uploaded_ids = filtered_data.values_list("viewuploaded", flat=True).distinct()
    papered_ids = filtered_data.values_list("viewpapered", flat=True).distinct()

    baseline_filter = baseline_data_billed.filter(
        Q(viewuploaded__in=uploaded_ids) |
        Q(viewpapered__in=[p for p in papered_ids if p is not None])
    )
    
    grouped_sums = defaultdict(float)
    total_sum_of_all_bill_dates = 0.0

    for item in baseline_filter:
        if item.viewuploaded_id:
            group_key = f"uploaded_{item.viewuploaded_id}"
        elif item.viewpapered_id:
            group_key = f"papered_{item.viewpapered_id}"
        else:
            group_key = "unknown"


        raw_charge = getattr(item, "total_charges", 0)
        if raw_charge is None:
            charge = 0.0
        else:
            if isinstance(raw_charge, str):
                raw_charge = re.sub(r"[^\d.\-]", "", raw_charge) 
            try:
                charge = float(raw_charge)
            except ValueError:
                charge = 0.0

        grouped_sums[group_key] += charge
        total_sum_of_all_bill_dates += charge

    response.append({
        "grouped_summary": dict(grouped_sums),
        "total_sum_of_all_bill_dates": round(total_sum_of_all_bill_dates, 2)
    })
    print(response)
    if is_download:
        reportObj = GenerateExcelReport(report_name="Payment Detail Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mobile_bills_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')

    approval_status = request.GET.get('approval_status')



    
    filtered_data = base_data_billed.filter(company=company, sub_company=sub_company)

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    filtered_data = filtered_data.filter(is_baseline_approved=approval_status)

    
    response = [model_to_dict(item, fields=["id", "invoicenumber", "bill_date", "accountnumber", "vendor", "net_amount", "is_baseline_approved"]) for item in filtered_data]

    uploaded_ids = filtered_data.values_list("viewuploaded", flat=True).distinct()
    papered_ids = filtered_data.values_list("viewpapered", flat=True).distinct()

    baseline_filter = baseline_data_billed.filter(
        Q(viewuploaded__in=uploaded_ids) |
        Q(viewpapered__in=[p for p in papered_ids if p is not None])
    )
    
    grouped_sums = defaultdict(float)
    total_sum_of_all_bill_dates = 0.0

    for item in baseline_filter:
        if item.viewuploaded_id:
            group_key = f"uploaded_{item.viewuploaded_id}"
        elif item.viewpapered_id:
            group_key = f"papered_{item.viewpapered_id}"
        else:
            group_key = "unknown"


        raw_charge = getattr(item, "total_charges", 0)
        if raw_charge is None:
            charge = 0.0
        else:
            if isinstance(raw_charge, str):
                raw_charge = re.sub(r"[^\d.\-]", "", raw_charge) 
            try:
                charge = float(raw_charge)
            except ValueError:
                charge = 0.0

        grouped_sums[group_key] += charge
        total_sum_of_all_bill_dates += charge

    response.append({
        "grouped_summary": dict(grouped_sums),
        "total_sum_of_all_bill_dates": round(total_sum_of_all_bill_dates, 2)
    })
    print(response)
    if is_download:
        reportObj = GenerateExcelReport(report_name="Mobile Bills Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_entered_bills_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    start_date = data.get('start_date')
    end_date = data.get('end_date')

    upload_by = request.GET.get('upload_by')

    
    filtered_data = base_data_billed.filter(company=company, sub_company="OSI")

    filtered_data = filter_by_range(data=filtered_data, start=start_date, end=end_date)

    upload_by = PortalUser.objects.filter(email=upload_by).first() if upload_by else None
    filtered_data = filtered_data.filter(uploaded_by=upload_by) if upload_by else filtered_data

    
    response = []
    for item in filtered_data:
        data = model_to_dict(item, fields=["id", "vendor", "accountnumber", "bill_date", "net_amount", "BillingName", "date_due", "variance", "created_at", "is_baseline_approved"])
        data["upload_by"] = upload_by  # Add the extra field after conversion
        response.append(data)
    print(response)
        

    uploaded_ids = filtered_data.values_list("viewuploaded", flat=True).distinct()
    papered_ids = filtered_data.values_list("viewpapered", flat=True).distinct()

    baseline_filter = baseline_data_billed.filter(
        Q(viewuploaded__in=uploaded_ids) |
        Q(viewpapered__in=[p for p in papered_ids if p is not None])
    )
    
    grouped_sums = defaultdict(float)
    total_sum_of_all_bill_dates = 0.0

    for item in baseline_filter:
        if item.viewuploaded_id:
            group_key = f"uploaded_{item.viewuploaded_id}"
        elif item.viewpapered_id:
            group_key = f"papered_{item.viewpapered_id}"
        else:
            group_key = "unknown"


        raw_charge = getattr(item, "total_charges", 0)
        if raw_charge is None:
            charge = 0.0
        else:
            if isinstance(raw_charge, str):
                raw_charge = re.sub(r"[^\d.\-]", "", raw_charge) 
            try:
                charge = float(raw_charge)
            except ValueError:
                charge = 0.0

        grouped_sums[group_key] += charge
        total_sum_of_all_bill_dates += charge

    response.append({
        "grouped_summary": dict(grouped_sums),
        "total_sum_of_all_bill_dates": round(total_sum_of_all_bill_dates, 2)
    })
    if is_download:
        reportObj = GenerateExcelReport(report_name="Entered Bills Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organization_location_listing_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    

    orgObj = Organizations.objects.filter(Organization_name=sub_company).first()
    if not orgObj:
        return Response({"message":"Organization not found!"}, status=status.HTTP_400_BAD_REQUEST)
    filtered_data = Location.objects.filter(organization=orgObj)


    
    response = [model_to_dict(item, exclude=["location_picture_1","location_picture_2","location_picture_3","location_picture_4"]) for item in filtered_data]

    if is_download:
        reportObj = GenerateExcelReport(report_name="Organization Location Listing", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
from .ReportSerializers import OrganizationLocationSerializer, InventorySerializer
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organization_location_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    

    orgObj = Organizations.objects.filter(Organization_name=sub_company).first()
    if not orgObj:
        return Response({"message":"Organization not found!"}, status=status.HTTP_400_BAD_REQUEST)
    filtered_data = Location.objects.filter(organization=orgObj)


    
    # response = [model_to_dict(item, exclude=["location_picture_1","location_picture_2","location_picture_3","location_picture_4"]) for item in filtered_data]
    response = OrganizationLocationSerializer(filtered_data, many=True).data
    if is_download:
        reportObj = GenerateExcelReport(report_name="Organization Location Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_Inactive_location_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')

    

    orgObj = Organizations.objects.filter(Organization_name=sub_company).first()
    if not orgObj:
        return Response({"message":"Organization not found!"}, status=status.HTTP_400_BAD_REQUEST)
    filtered_data = Location.objects.filter(organization=orgObj)

    filtered_data = filtered_data.filter(Q(location_type="Closed") | Q(location_type="Inactive Site"))

    
    response = [model_to_dict(item, exclude=["location_picture_1","location_picture_2","location_picture_3","location_picture_4", "created", "updated"]) for item in filtered_data]
    print(response)
    if is_download:
        reportObj = GenerateExcelReport(report_name="Inactive Location Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_filter_location_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))
    
    sub_company = data.get('sub_company')
    company = data.get('company')
    location_type = data.get('location_status')
    

    orgObj = Organizations.objects.filter(Organization_name=sub_company).first()
    if not orgObj:
        return Response({"message":"Organization not found!"}, status=status.HTTP_400_BAD_REQUEST)
    filtered_data = Location.objects.filter(organization=orgObj)

    filtered_data = filtered_data.filter(location_type=location_type)

    
    response = [model_to_dict(item, exclude=["location_picture_1","location_picture_2","location_picture_3","location_picture_4"]) for item in filtered_data]

    if is_download:
        reportObj = GenerateExcelReport(report_name="Filtered Location Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ban_by_location_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
    ban_status = request.GET.get('ban_status')
    location = request.GET.get('location')



    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    filtered_data = filtered_data.filter(location=location)
    filtered_data = filtered_data.filter(banstatus=ban_status) if ban_status else filtered_data


    response = [model_to_dict(item, fields=["id", "bill_date", "sub_company", "net_amount", "vendor","BillingName","BillingAdd", "BillingState", "BillingZip", "BillingCity", "BillingCountry",]) for item in filtered_data]
    print(response)

    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Ban by Location Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ban_by_vendor_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
    ban_status = request.GET.get('ban_status')
    vendor = request.GET.get('vendor')
    location = request.GET.get('location')



    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    filtered_data = filtered_data.filter(vendor=vendor) if vendor else filtered_data
    filtered_data = filtered_data.filter(location=location) if location else filtered_data
    filtered_data = filtered_data.filter(banstatus=ban_status) if ban_status else filtered_data

    print(filtered_data)


    response = [model_to_dict(item, fields=["id", "vendor", "ban", "location", "BillingName","BillingAdd", "BillingState", "BillingZip", "BillingCity", "BillingCountry", ]) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Ban by vendor Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_Inactive_bans_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')



    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    filtered_data = filtered_data.filter(Q(banstatus="Closed") | Q(banstatus="Inactive"))


    response = [model_to_dict(item) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Inactive bans Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_asset_tracking_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
    location = request.GET.get('location')



    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    filtered_data = filtered_data.filter(location=location)


    response = [model_to_dict(item) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Asset tracking Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_asset_transactions_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
    location = request.GET.get('location')
    Asset = data.get('Asset')
    Transacton_Type = data.get('Transacton_Type')



    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    filtered_data = filtered_data.filter(location=location)


    response = [model_to_dict(item) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Asset transactions Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_outstanding_loaners_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
    location = request.GET.get('location')
 


    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    filtered_data = filtered_data.filter(location=location)


    response = [model_to_dict(item) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Outstanding loaners Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_order_tracking_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
    vendor = request.GET.get('vendor')
 


    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    filtered_data = filtered_data.filter(vendor=vendor)


    response = [model_to_dict(item) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Order tracking Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contact_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
    vendor = request.GET.get('vendor')
 


    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    filtered_data = filtered_data.filter(vendor=vendor)


    response = [model_to_dict(item) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Contact Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ban_autopay_listing_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
 


    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)


    response = [model_to_dict(item, fields=["accountnumber","location", "vendor"]) for item in filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Ban autopay listing Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_phone_list_byOrg_report(request):
    data = request.GET
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
 


    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    unique_filtered_data = unique_data_onboarded.filter(account_number__in=filtered_data.values_list("accountnumber", flat=True))



    response = [model_to_dict(item, fields=["account_number","wireless_number", "user_name"]) for item in unique_filtered_data]
    print(response)


    if is_download:
        reportObj = GenerateExcelReport(report_name="Phone list by organization Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_inventory_report(request):
    data = request.GET
    print(data)
    is_download = is_bool(data.get('is_download',False))

    
    sub_company = data.get('sub_company')
    company = data.get('company')
    ban_status = request.GET.get('ban_status')
    location = request.GET.get('location')



    filtered_data = base_data_onboarded.filter(company=company, sub_company=sub_company)

    filtered_data = filtered_data.filter(location=location)
    filtered_data = filtered_data.filter(banstatus=ban_status) if ban_status else filtered_data

    account_numbers = filtered_data.values_list("accountnumber", flat=True)
    filtered_data = unique_data_onboarded.filter(account_number__in=account_numbers)


    response = InventorySerializer(filtered_data, many=True).data


    if is_download:
        reportObj = GenerateExcelReport(report_name="Inventory Report", data=response)
        report, report_name = reportObj._generate()
        Fileresponse = HttpResponse(
            report.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        Fileresponse['Content-Disposition'] = f'attachment; filename="{report_name}"'
        return Fileresponse
    else:
        return Response({"data":response}, status=status.HTTP_200_OK)