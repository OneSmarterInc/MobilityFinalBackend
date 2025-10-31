# filters.py
from dateutil import parser as dateparser
from django.db.models import Q


def parse_date_param(s):
    if not s:
        return None
    try:
        return dateparser.parse(s).date()
    except Exception:
        return None

def apply_common_filters(qs, request):
    # ✅ uploaded bills only (FK present)
    qs = qs.filter(
        Q(viewuploaded__isnull=False) | Q(viewpapered__isnull=False)
    )

    company = request.query_params.get("company")
    sub_company = request.query_params.get("sub_company")
    vendor = request.query_params.get("vendor")
    year = request.query_params.get("year")
    month = request.query_params.get("month")
    accountnumber = request.query_params.get("accountnumber")

    if company:
        qs = qs.filter(company__iexact=company)
    if sub_company:
        qs = qs.filter(sub_company__iexact=sub_company)
    if vendor:
        qs = qs.filter(vendor__iexact=vendor)
    if accountnumber:
        qs = qs.filter(accountnumber__iexact=accountnumber)    

    if year:
        qs = qs.filter(year=str(year))
    if month:
        qs = qs.filter(month=str(month))

    # optional date range (parsed later in view if you kept that logic)
    request._analytics_date_from = parse_date_param(request.query_params.get("date_from"))
    request._analytics_date_to = parse_date_param(request.query_params.get("date_to"))
    return qs




# app/analytics/ba_filters.py
def apply_ba_filters(qs, request):
    company = request.query_params.get("company")
    vendor = request.query_params.get("vendor")
    account = request.query_params.get("accountnumber")
    year = request.query_params.get("year")
    month = request.query_params.get("month")

    if company: qs = qs.filter(company__iexact=company)
    if vendor: qs = qs.filter(vendor__iexact=vendor)
    if account: qs = qs.filter(account_number__iexact=account)
    if year: qs = qs.filter(bill_year=str(year))
    if month: qs = qs.filter(bill_month=str(month))
    return qs
