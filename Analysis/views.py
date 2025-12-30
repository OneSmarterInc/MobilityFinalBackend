from django.shortcuts import render, HttpResponse

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Analysis
from .ser import AnalysisSaveSerializer, AnalysisShowSerializer, VendorsShowSerializer, MultipleAnalysisSerializer,MultipleAnalysisShowSerializer
from Dashboard.ModelsByPage.DashAdmin import Vendors
from .Background.task import Process_Analysis_PDF, Process_multiple_pdfs
from authenticate.views import saveuserlog
from checkbill import prove_bill_ID, check_tmobile_type
from django.core.files.base import File
from django.conf import settings
from .models import AnalysisData, MultipleFileUpload
from .models import SummaryData
from Dashboard.ModelsByPage.aimodels import BotChats
from Dashboard.Serializers.chatser import ChatSerializer
from dateutil import parser
from Batch.views import create_notification
from django.db.models import Sum, Count, F, Case, When, DecimalField, Value
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated 
import os,re
import zipfile
import numpy as np
from datetime import datetime
import pandas as pd
from addon import extract_data_from_zip, has_field
import json, os, zipfile
import traceback




class AnalysisView(APIView):
    permission_classes = [IsAuthenticated]
    # from django.utils import timezone
    # today = timezone.now().date()
    # print("weekday==",today.strftime("%A"))

    def get(self, request, pk=None):
        if pk is None:
            org = request.user.organization
            analysis = Analysis.objects.filter(created_by=request.user) if org else Analysis.objects.all()
            vendors = Vendors.objects.all()
            Vser = VendorsShowSerializer(vendors, many=True)
            ser = AnalysisShowSerializer(analysis, many=True)
            return Response({"data": ser.data, 'vendors':Vser.data}, status=status.HTTP_200_OK)
        else:
            try:
                analysis = Analysis.objects.get(id=pk)
                ser = AnalysisShowSerializer(analysis)
                return Response({"data": ser.data}, status=status.HTTP_200_OK)
            except Analysis.DoesNotExist:
                return Response({"message": "File not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            filename = request.data['uploadBill'].name
            check = prove_bill_ID(vendor_name=request.data['vendor'],bill_path=request.data['uploadBill']) if filename.endswith('.pdf') else True
            if not check:
                return Response({"message": f"Invalid file: expected a {request.data['vendor']} file."},status=status.HTTP_400_BAD_REQUEST)
            
            if filename.endswith('.pdf') and "mobile" in request.data['vendor'].lower():
                type = check_tmobile_type(request.data['uploadBill'])
                if type == 0:
                    return Response({"message": "Unable to analyze pdf. Please upload valid T-Mobile bill."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                type = None
            ser = AnalysisSaveSerializer(data=request.data)
            if ser.is_valid():
                ser.save()
            else:
                print(ser.errors)
                return Response({"message": "Unable to analyze pdf."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                id = ser.data['id']
                obj = Analysis.objects.filter(id=id).first()
                buffer_data = json.dumps(
                        {'pdf_path':obj.uploadBill.path, 'vendor_name':obj.vendor.name, 'pdf_filename':obj.uploadBill.name, 'user_id':obj.created_by.id, 'organization':obj.client, 'remark':obj.remark, 'first_name':obj.created_by.first_name, 'last_name':obj.created_by.last_name, 'store':"", 'type':type, "user_email":request.user.email}
                    )
                if filename.endswith('.pdf'):
                    saveuserlog(
                        request.user,
                        f"{request.user.email} uploaded {obj.vendor.name} file for client {obj.client} for analysis"
                    )
                    Process_Analysis_PDF.delay(buffer_data, obj.id)
                    return Response({"message":f"File Analysis is in progress,It will take some time.\n Please check analysis page later."},status=status.HTTP_200_OK)
                elif filename.endswith('.zip'):
                    zip_instance = ZipAnalysis(buffer_data, instance=obj)
                    check,msg = zip_instance.process()
                    if not check:
                        return Response({"message":"Unable to process rdd file may be due to unsupported file format."},status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({"message": "RDD uploaded successfully."},status=status.HTTP_200_OK)
                elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                    excel_instance = ExcelAnalysis(instance=obj)
                    check,msg = excel_instance.process()
                    if not check:
                        return Response({"message":"Unable to process excel file may be due to unsupported file format."},status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({"message": "Excel uploaded successfully."},status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Only PDF, ZIP, and Excel files are supported."}, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                print(e)
                return Response({"message": f'Error processing file!{str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print(e)
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk):
        try:
            analysis = Analysis.objects.get(id=pk)
            ser = AnalysisSaveSerializer(analysis, data=request.data)
            if ser.is_valid():
                ser.save()
                return Response({"message": "pdf analysis updated successfully!", "data": ser.data}, status=status.HTTP_200_OK)
        except Analysis.DoesNotExist:
            return Response({"message": "pdf not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": "Internal Server Error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        try:
            analysis = Analysis.objects.get(id=pk)
            vendor = analysis.vendor.name
            client = analysis.client
            file = analysis.uploadBill.name
            analysis.delete()
            saveuserlog(
                request.user,
                f"{request.user.email} deleted {vendor} file '{file}' for client {client if client else '-'} from Analysis"
            )

            return Response({"message": "Analysis file deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Analysis.DoesNotExist:
            return Response({"message": "Analysis file not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"message": "Internal Server Error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    

class download_analysis_xlsx_file(APIView):
    def get(self,request,pk):
        workbook = Analysis.objects.get(id=pk)
        excel_data = workbook.excel
        response = HttpResponse(excel_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={workbook.excel.name}'
        return response  
    
class MultipleUploadView(APIView):
    def __init__(self, **kwargs):
        self.is_pdf = False
        self.pdf_files = []
    def get(self,request,pk=None,*args,**kwargs):
        org = request.user.organization
        if pk is None:
            analysis = MultipleFileUpload.objects.filter(created_by=request.user) if org else MultipleFileUpload.objects.all()
            vendors = Vendors.objects.all()
            Vser = VendorsShowSerializer(vendors, many=True)
            ser = MultipleAnalysisShowSerializer(analysis, many=True)
            return Response({"data": ser.data, 'vendors':Vser.data}, status=status.HTTP_200_OK)
        else:
            try:
                analysis = MultipleFileUpload.objects.get(id=pk)
                ser = MultipleAnalysisShowSerializer(analysis)
                return Response({"data": ser.data}, status=status.HTTP_200_OK)
            except Analysis.DoesNotExist:
                return Response({"message": "File not found"}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def post(self, request, *args, **kwargs):
        data = request.data
        vendor = data.get('vendor')

        # Collect uploaded files (1–3 allowed)
        files = [data.get(f'file{i}') for i in range(1, 4)]

        files = [f for f in files if f not in (None, "NULL", "null")]  # remove None

        if not files:
            return Response({"message": "At least one file is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate extensions (allow only PDF/ZIP)
        for f in files:
            if f.name.lower().endswith(".pdf"):
                self.is_pdf = True
                self.pdf_files.append(f)
            if not (f.name.lower().endswith(".pdf") or f.name.lower().endswith(".zip")):
                return Response({"message": "Invalid file type. Only PDF or ZIP files are allowed."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate vendor correctness
        for f in self.pdf_files:
            if not prove_bill_ID(vendor_name=vendor, bill_path=f):
                return Response(
                    {"message": "One or more uploaded pdf bills do not match the expected vendor."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Validate T-Mobile type consistency (if vendor is T-Mobile)
        tmobile_type = None
        if "mobile" in vendor.lower():
            types = []
            for f in self.pdf_files:
                t_type = check_tmobile_type(f)
                if t_type == 0:
                    return Response({"message": "Unable to analyze pdf. Please upload valid T-Mobile bill."}, status=status.HTTP_400_BAD_REQUEST)
                types.append(t_type)

            if len(set(types)) > 1:
                return Response(
                    {"message": "Mismatch detected: The uploaded T-Mobile bills are not of the same type."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                tmobile_type = types[0]

        # Save serializer
        ser = MultipleAnalysisSerializer(data=data)
        if ser.is_valid():
            ser.save()
        else:
            print(ser.errors)
            return Response({"message": "Unable to analyze pdf."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            obj = MultipleFileUpload.objects.filter(id=ser.data['id']).first()

            # Build buffer_data dynamically
            buffer_data = {}
            if obj.file1: buffer_data.update({"file1_path": obj.file1.path})
            if obj.file2: buffer_data.update({"file2_path": obj.file2.path})
            if obj.file3: buffer_data.update({"file3_path": obj.file3.path})

            buffer_data.update({
                'company':request.user.company.Company_name if request.user.company else "",
                'vendor': obj.vendor.name,
                'type': tmobile_type,
                'user_email': request.user.email,
            })
            saveuserlog(
                request.user,
                f"{request.user.email} uploaded {len(files)} {obj.vendor.name} file(s) for client {obj.client} for analysis"
            )
            create_notification(
                request.user,
                f"{request.user.email} uploaded {len(files)} {obj.vendor.name} file(s) for client {obj.client} for analysis", request.user.company
            )
            Process_multiple_pdfs.delay(buffer_data, obj.id)
            return Response(
                {"message": "Analysis is in progress.\nIt will take some time. Please check analysis page later."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            if obj and obj.pk : obj.delete()
            return Response({"message": f"Error processing files, may be due to internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
    def delete(self, request, pk):
        try:
            analysis = MultipleFileUpload.objects.get(id=pk)
            vendor = analysis.vendor.name
            client = analysis.client
            analysis.delete()
            saveuserlog(
                request.user,
                f"{request.user.email} deleted {vendor} analysis files of client {client if client else '-'}"
            )
            create_notification(
                request.user,
                f"{request.user.email} deleted {vendor} analysis files of client {client if client else '-'}", request.user.company
            )
            return Response({"message": "Analysis files deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Analysis.DoesNotExist:
            return Response({"message": "Analysis files not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({"message": "Internal Server Error!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

        

class ZipAnalysis:
    def __init__(self,buffer_data, instance):
        self.instance = instance
        self.buffer_data = json.loads(buffer_data) if isinstance(buffer_data, str) else buffer_data

        # Collect up to 3 file paths dynamically
        self.file_paths = [self.buffer_data.get(f"file{i}_path") for i in range(1, 4)]
        self.file_paths = [f for f in self.file_paths if f]  # remove None values

        # Collect filenames safely
        self.file_names = [os.path.basename(f) for f in self.file_paths]
        self.vendor = self.buffer_data.get('vendor')
        self.type = self.buffer_data.get('type')

        self.account_number = None
        self.all_plans = []
        self.plan_charges = {}

    def add_gb(self, val):
        if pd.isna(val):   # leave NaN as is
            return val
        val_str = str(val).strip()
        if val_str.lower().endswith("gb"):
            return val_str
        return f"{val_str} GB"

    def split_sheets(self, datadf):
        # Make a copy to avoid warnings
        datadf = datadf.copy()

        # Define column mapping
        cols = {
            "Wireless Number": "Wireless Number",
            "Username": "User Name",
            "Plan": "Current Plan",
            "Data Usage": "Data Usage (GB)",
            "Monthly Charges": "Charges",
            "Recommended Plan": "Recommended Plan",
            "Recommended Plan Charges": "Recommended Plan Charges",
            "Recommended Plan Savings": "Recommended Plan Savings",
        }

        # Select only available columns + add missing ones as empty
        base_df = datadf[list(cols.keys() & datadf.columns)].copy()
        for col in cols.keys():
            if col not in base_df.columns:
                base_df[col] = None

        # Rename columns
        base_df = base_df.rename(columns=cols)

        # Reorder columns
        column_order = [
            "Wireless Number",
            "User Name",
            "Current Plan",
            "Data Usage (GB)",
            "Charges",
            "Recommended Plan",
            "Recommended Plan Charges",
            "Recommended Plan Savings",
        ]
        base_df = base_df[column_order]

        # --- Recommendation Logic ---
        plan_charges_float = {
            p: float(c.replace("$", "")) if isinstance(c, str) else float(c)
            for p, c in self.plan_charges.items()
        }


        def extract_gb(plan_name: str):
            if not plan_name:
                return None
            match = re.search(r"(\d+(?:\.\d+)?)\s*GB", plan_name.upper())
            if match:
                try:
                    return float(match.group(1))
                except:
                    return None
            return None

        def suggest_plan(row):
            current_plan = row["Current Plan"]
            try:
                current_charge = float(str(row["Charges"]).replace("$", "").strip())
            except:
                return pd.Series([None, None, None])  # Invalid charges

            usage_val = row["Data Usage (GB)"]
            if pd.isna(usage_val) or usage_val == "NA":
                return pd.Series([None, None, None])

            try:
                usage = float(str(usage_val).upper().replace("GB", "").strip())
            except:
                usage = 0.0

            candidate_plans = []
            for plan in self.all_plans:
                gb_limit = extract_gb(plan)
                if gb_limit is not None and usage <= gb_limit:
                    candidate_plans.append((plan, plan_charges_float.get(plan, float("inf"))))
            if candidate_plans:
                recommended_plan, rec_charge = min(candidate_plans, key=lambda x: x[1])
                if recommended_plan != current_plan and rec_charge < current_charge:
                    savings = float(current_charge - rec_charge)
                    savings_str = f"${savings:.2f}"
                    rec_charge_str = f"${rec_charge:.2f}"
                    return pd.Series([recommended_plan, rec_charge_str, savings_str])

            return pd.Series([None, None, None])
        base_df[["Recommended Plan", "Recommended Plan Charges", "Recommended Plan Savings"]] = base_df.apply(suggest_plan, axis=1)

        # --- Handle NA usage ---
        na_df = base_df[base_df["Data Usage (GB)"] == "NA"].copy()
        non_na_df = base_df[base_df["Data Usage (GB)"] != "NA"].copy()

        # Convert NA usage to 0 for non-unlimited plans → push to zero usage sheet
        na_non_unlimited = na_df[~na_df["Current Plan"].str.contains("Unlimited", case=False, na=False)].copy()
        na_non_unlimited["Data Usage (GB)"] = "0"  # treat NA as 0

        # Unlimited NA plans remain separate
        sheet6 = na_df[na_df["Current Plan"].str.contains("Unlimited", case=False, na=False)].copy()

        # Merge NA-non-unlimited into non_na_df
        non_na_df = pd.concat([non_na_df, na_non_unlimited], ignore_index=True)

        # Now bucketize usage
        print("Now bucketize usage")
        data_usage = (
            non_na_df["Data Usage (GB)"]
            .astype(str)                      # ensure string
            .str.replace("GB", "", regex=False)
            .replace("nan", pd.NA)            # handle NaN safely
            .astype(float)                    # back to float
        )


        sheet2 = non_na_df[data_usage <= 0].copy()  # includes NA converted to 0
        sheet3 = non_na_df[(data_usage > 0) & (data_usage <= 5)].copy()
        sheet4 = non_na_df[(data_usage > 5) & (data_usage <= 15)].copy()
        sheet5 = non_na_df[data_usage > 15].copy()

        print("All sheets processed")

        return sheet2, sheet3, sheet4, sheet5, sheet6


    def add_no_recommendation(self,dfs):

        for df in dfs:
            if all(col in df.columns for col in [
                "Recommended Plan",
                "Recommended Plan Charges",
                "Recommended Plan Savings"
            ]):
                mask = (
                    df["Recommended Plan"].isna() &
                    df["Recommended Plan Charges"].isna() &
                    df["Recommended Plan Savings"].isna()
                )
                df.loc[mask, ["Recommended Plan",
                            "Recommended Plan Charges",
                            "Recommended Plan Savings"]] = "No recommendation needed"
        return dfs
    
    def check_availability(self, all_dfs):
        combined = []

        for df in all_dfs:
            if df.empty:
                continue
            subdf = df[["Wireless Number", "Bill Date"]].dropna().copy()
            subdf["Status"] = "present"
            combined.append(subdf)

        if not combined:
            return pd.DataFrame() 

        combined_df = pd.concat(combined, ignore_index=True)

        result = combined_df.pivot_table(
            index="Wireless Number",
            columns="Bill Date",
            values="Status",
            aggfunc="first",  
            fill_value="absent"
        ).reset_index()

        status_cols = [c for c in result.columns if c != "Wireless Number"]
        mask_all_present = result[status_cols].eq("present").all(axis=1)
        result = result[~mask_all_present]

        bill_dates_sorted = sorted(
        status_cols, key=lambda x: self.parse_bill_date(str(x))
        )
        result = result[["Wireless Number"] + bill_dates_sorted]

        return result
    
    def normalize_usage(self, val):
        if pd.isna(val) or str(val).strip().upper() == "NA":
            return np.nan
        s = str(val).strip().lower()
        # Extract numeric part
        match = re.search(r"([\d\.]+)", s)
        if not match:
            return np.nan
        num = float(match.group(1))
        # Check unit (default GB if missing)
        if "tb" in s:
            return num * 1024
        elif "mb" in s:
            return num / 1024
        else:  # assume GB
            return num
    
    def check_usage_trend(self, all_dfs):
        combined = []

        for df in all_dfs:
            if df.empty:
                continue
            subdf = df[["Wireless Number", "Bill Date", "Data Usage"]].copy()

            # Keep original bill date and data usage
            subdf["Bill Date Original"] = subdf["Bill Date"].astype(str)
            subdf["Data Usage Original"] = subdf["Data Usage"].astype(str)

            # Numeric conversion for calculation
            subdf["Data Usage"] = subdf["Data Usage"].apply(self.normalize_usage)

            # Parsed date for chronological sorting
            subdf["Parsed Date"] = subdf["Bill Date"].apply(self.parse_bill_date)

            combined.append(subdf)

        if not combined:
            return pd.DataFrame()

        combined_df = pd.concat(combined, ignore_index=True)

        # Sort for consistency
        combined_df.sort_values(["Wireless Number", "Parsed Date"], inplace=True)

        # Keep only latest 3 bill dates per Wireless Number
        combined_df = combined_df.groupby("Wireless Number").tail(3)

        # === Display table (original usage values) ===
        usage_wide = combined_df.pivot_table(
            index="Wireless Number",
            columns="Bill Date Original",
            values="Data Usage Original",
            aggfunc="first"
        )

        # Ensure chronological order of columns
        bill_date_order = (
            combined_df.drop_duplicates("Bill Date Original")
            .sort_values("Parsed Date")["Bill Date Original"]
            .tolist()
        )
        usage_wide = usage_wide.reindex(columns=bill_date_order)

        # === Calculation table (numeric values only) ===
        calc_base = combined_df.pivot_table(
            index="Wireless Number",
            columns="Bill Date Original",
            values="Data Usage",
            aggfunc="first"
        )
        calc_base = calc_base.reindex(columns=bill_date_order)

        # Calculate variance between top 2 usage months
        def calc_stats(row):
            if row.isna().all():  # all values are NA
                return "NA", "NA"
            vals = row.dropna().to_dict()
            if len(vals) < 2:
                return "-", "-"
            # Sort by usage descending
            sorted_vals = sorted(vals.items(), key=lambda x: x[1], reverse=True)
            (m1, v1), (m2, v2) = sorted_vals[0], sorted_vals[1]

            if v2 == 0:
                return "∞", f"{pd.to_datetime(m1).strftime('%b %Y')} > {pd.to_datetime(m2).strftime('%b %Y')}"

            variance = ((v1 - v2) / v2) * 100
            relation = f"{pd.to_datetime(m1).strftime('%b %Y')} > {pd.to_datetime(m2).strftime('%b %Y')}" if v1 > v2 else f"{pd.to_datetime(m2).strftime('%b %Y')} > {pd.to_datetime(m1).strftime('%b %Y')}"
            return f"{variance:.2f}%", relation


        stats = calc_base.apply(calc_stats, axis=1, result_type="expand")
        stats.columns = ["Variance", "Relation"]

        # Merge stats with display table
        usage_wide = usage_wide.reset_index().merge(
            stats.reset_index(), on="Wireless Number", how="left"
        )

        # Replace NaN with "NA" in display columns only
        bill_date_cols = [c for c in usage_wide.columns if c not in ["Wireless Number", "Variance", "Relation"]]
        usage_wide[bill_date_cols] = usage_wide[bill_date_cols].fillna("NA")

        # Final check: if all bill dates are "NA", force stats to "NA"
        mask_all_na = usage_wide[bill_date_cols].eq("NA").all(axis=1)
        usage_wide.loc[mask_all_na, ["Variance", "Relation"]] = "NA"

        # === Keep only rows with variance > 10% ===
        def is_valid_variance(v):
            try:
                return float(v.strip("%")) > 10
            except:
                return False

        usage_wide = usage_wide[usage_wide["Variance"].apply(is_valid_variance)]

        return usage_wide


    def export_to_excel(self, original_dfs, line_items, filename="usage_report.xlsx"):
        sheet2, sheet3, sheet4, sheet5, sheet6 = self.split_sheets(line_items)
        STARTROW = 2
        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            excel_sheet2, excel_sheet3, excel_sheet4, excel_sheet5, excel_sheet6 = self.add_no_recommendation([sheet2, sheet3, sheet4, sheet5, sheet6])
            sheet7 = self.check_availability(original_dfs)
            sheet8 = self.check_usage_trend(original_dfs)
            for i, df in enumerate(original_dfs):
                if df.empty:
                    continue
                df.drop(columns=[c for c in ['file_name','bill_day','bill_month','bill_year'] if c in df.columns], inplace=True)
                bill_date = str(df.get("Bill Date", [f"Sheet{i+1}"]).iloc[0]) \
                    if "Bill Date" in df.columns else f"Original_{i+1}"
                df.to_excel(writer, sheet_name=str(bill_date), index=False, startrow=STARTROW)
            max_usage = line_items
            max_usage.drop(columns=[c for c in ['bill_day','bill_month','bill_year'] if c in max_usage.columns], inplace=True)
            max_usage = max_usage.drop(columns=['file_name'])
            max_usage.to_excel(writer, sheet_name="Maximum Usage from all files", index=False, startrow=STARTROW)
            excel_sheet2.to_excel(writer, sheet_name="Zero Usage Line", index=False, startrow=STARTROW)
            excel_sheet3.to_excel(writer, sheet_name="< 5GB", index=False, startrow=STARTROW)
            excel_sheet4.to_excel(writer, sheet_name="5 to 15GB", index=False, startrow=STARTROW)
            excel_sheet5.to_excel(writer, sheet_name="> 15GB", index=False, startrow=STARTROW)
            excel_sheet6.to_excel(writer, sheet_name="NA - Unlimited", index=False, startrow=STARTROW)
            sheet7.to_excel(writer, sheet_name="Attendance", index=False, startrow=STARTROW)
            sheet8.to_excel(writer, sheet_name="Data Usage Trend", index=False, startrow=STARTROW)

            # 🔥 Add note INSIDE the context
            workbook = writer.book
            title_format = workbook.add_format({
                "bold": True, "font_size": 14, "align": "left", "valign": "vcenter"
            })
            header_format = workbook.add_format({
                "bold": True, "align": "center", "valign": "vcenter", "text_wrap": True
            })
            center_format = workbook.add_format({
                "align": "center", "valign": "vcenter"
            })

          
            def apply_sheet_format(sheet_name, df_for_columns):
                ws = writer.sheets[sheet_name]
                ncols = len(df_for_columns.columns)
                if ncols == 0:
                    return

                heading_map = {
                    "Maximum Usage from all files": "Maximum Usage from all files",
                "Zero Usage Line": "Zero Usage Line",
                "< 5GB": "Less Than 5GB",
                "5 to 15GB": "Between 5 To 15 GB",
                "> 15GB": "Greater than 15 GB",
                "NA - Unlimited": "Unlimited Plan With Data Usage N/A",
                "Attendance": "Attendance of wireless numbers",
                "Data Usage Trend": "Data usage trend over the months"
                }

                heading_text = heading_map.get(sheet_name, sheet_name)

                ws.merge_range(0, 0, 0, ncols - 1, heading_text, title_format)

                ws.set_row(STARTROW, 20, header_format)

                for col_idx, col_name in enumerate(df_for_columns.columns):
                    header_w = len(str(col_name)) + 2
                    col_series = df_for_columns[col_name].fillna("").astype(str)
                    sample = col_series.iloc[:200] 
                    content_w = sample.map(len).max() if not sample.empty else 0
                    content_w = content_w + 2
                    width = max(8, min(60, max(header_w, content_w)))
                    ws.set_column(col_idx, col_idx, width, center_format)

            for i, df in enumerate(original_dfs):
                if df.empty:
                    continue
                bill_date = str(df.get("Bill Date", [f"Sheet{i+1}"]).iloc[0]) \
                    if "Bill Date" in df.columns else f"Original_{i+1}"
                apply_sheet_format(str(bill_date), df)

            apply_sheet_format("Maximum Usage from all files", line_items)
            apply_sheet_format("Zero Usage Line", excel_sheet2)
            apply_sheet_format("< 5GB", excel_sheet3)
            apply_sheet_format("5 to 15GB", excel_sheet4)
            apply_sheet_format("> 15GB", excel_sheet5)
            apply_sheet_format("NA - Unlimited", excel_sheet6)
            apply_sheet_format("Attendance", sheet7)
            apply_sheet_format("Data Usage Trend", sheet8)

            ws_zero = writer.sheets["Zero Usage Line"]
            last_data_row_index = STARTROW + 1 + len(excel_sheet2)  # header + data
            note_row = last_data_row_index + 1
            note_text = (
                "Note: Wireless numbers with non-unlimited plans with no reported "
                "data usage are assumed to have 0 GB usage."
            )
            note_format = workbook.add_format({
                "italic": True, "align": "left", "valign": "top", "text_wrap": True
            })
            if len(excel_sheet2.columns) > 0:
                ws_zero.merge_range(
                note_row, 0, note_row, len(excel_sheet2.columns) - 1, note_text, note_format
                )
            # 🔥 Add note to "Data Usage Trend" sheet
            ws_trend = writer.sheets["Data Usage Trend"]
            last_data_row_index_trend = STARTROW + 1 + len(sheet8)  # header + data
            note_row_trend = last_data_row_index_trend + 1
            trend_note_text = (
                "Note: Only wireless numbers with variance greater than 10% are shown. "
                "Variance is calculated using the two highest usage months. "
                "If fewer than two bills are available, values are marked as '-'."
            )

            trend_note_format = workbook.add_format({
                "italic": True, "align": "left", "valign": "top", "text_wrap": True
            })
            if len(sheet8.columns) > 0:
                ws_trend.merge_range(
                    note_row_trend, 0, note_row_trend, len(sheet8.columns) - 1,
                    trend_note_text, trend_note_format
                )

        # Now the file is fully written
        target_dir = os.path.join(settings.MEDIA_ROOT, "BillAnalysis")
        os.makedirs(target_dir, exist_ok=True)

        with open(filename, "rb") as f:
            django_file = File(f)
            self.instance.excel.save(os.path.basename(filename), django_file)

        self.instance.is_processed = True
        self.instance.save()

        # cleanup
        os.remove(filename)

        # Add metadata for all sheets
        sheet2["data_type"] = "zero_usage"
        sheet3["data_type"] = "less_than_5_gb"
        sheet4["data_type"] = "between_5_and_15_gb"
        sheet5["data_type"] = "more_than_15_gb"
        sheet6["data_type"] = "NA_unlimited"

        all_data = pd.concat([sheet2, sheet3, sheet4, sheet5, sheet6], ignore_index=True)

        all_data = all_data.merge(
            line_items[["Wireless Number", "Account Number", "Bill Date"]],
            on="Wireless Number",
            how="left"
        )

        all_data = all_data.rename(columns={
            "Account Number": "account_number",
            "Bill Date": "bill_date",
            "Wireless Number": "wireless_number",
            "User Name": "user_name",
            "Current Plan": "current_plan",
            "Charges": "current_plan_charges",
            "Data Usage (GB)": "current_plan_usage",
            "Recommended Plan": "recommended_plan",
            "Recommended Plan Charges": "recommended_plan_charges",
            "Recommended Plan Savings": "recommended_plan_savings",
        })

        all_data["multiple_analysis_id"] = self.instance.id
    
        all_data["is_plan_recommended"] = all_data["recommended_plan"] != "No recommendation needed"
        all_data["recommended_plan"] = all_data["recommended_plan"].replace("No recommendation needed","")
        


        return all_data

    
    def add_data_to_db(self, data_df):
        print("saving to db")
        # convert charges and savings to numeric, errors='coerce' will set invalid parsing as NaN
        for col in ["current_plan_charges", "recommended_plan_charges", "recommended_plan_savings"]:
            data_df[col] = (
                data_df[col]
                .astype(str)  # make sure everything is a string
                .str.replace("$", "", regex=False)
                .replace("nan", "")  # remove "nan" strings
            )
            data_df[col] = pd.to_numeric(data_df[col], errors="coerce")  # convert to float

        data_df["current_plan_usage"] = data_df["current_plan_usage"].apply(self.add_gb)
        data_df["current_plan_charges"] = data_df["current_plan_charges"].astype(str).str.replace("$", "", regex=False)
        
        data_df["recommended_plan_charges"] = (
            data_df["recommended_plan_charges"]
            .replace("nan", np.nan)   # convert string "nan" → proper NaN
            .astype(str)
            .str.replace("$", "", regex=False)
        )

        # Finally convert to decimal/float
        data_df["recommended_plan_charges"] = data_df["recommended_plan_charges"].astype(float)
        # just create new entries, even if wireless_number already exists
        for _, row in data_df.iterrows():
            obj = AnalysisData.objects.create(
                account_number=row["account_number"],
                bill_date=row["bill_date"],
                wireless_number=row["wireless_number"],
                multiple_analysis_id=row["multiple_analysis_id"],
                data_type=row["data_type"],
                user_name=row["user_name"],
                is_plan_recommended=row["is_plan_recommended"],
                file_name=row["file_name"],
                current_plan=row["current_plan"],
                current_plan_charges=row["current_plan_charges"] if pd.notna(row["current_plan_charges"]) else None,
                current_plan_usage=row["current_plan_usage"],
                recommended_plan=row["recommended_plan"],
                recommended_plan_charges=row["recommended_plan_charges"] if pd.notna(row["recommended_plan_charges"]) else None,
                recommended_plan_savings=row["recommended_plan_savings"] if pd.notna(row["recommended_plan_savings"]) else None,
            )
        
    def get_dataframe(self, path):
        file_path = path.split("/")[-1]        
        name, ext = file_path.rsplit(".", 1)     
        ext = "." + ext                          

        if "_" in name:
            name = name.rsplit("_", 1)[0]

        file_name = f"{name}{ext}"
        dataframes = extract_data_from_zip(path)
        if not dataframes:
            return {"message": "No readable files found in zip", "error": -1}

        unique_dfs = [df for df in dataframes if "Wireless Number" in df.columns and df["Wireless Number"].is_unique]

        if unique_dfs:
            second_largest_df = unique_dfs[0]  
        else:
            second_largest_df = dataframes[0]  

        second_largest_df = second_largest_df.copy()

        second_largest_df = second_largest_df[second_largest_df["Wireless Number"].str.match(r'^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', na=False)]
        second_largest_df["Your Calling Plan"] = second_largest_df["Your Calling Plan"].apply(
            lambda x: str(x).split('$')[0].strip() if pd.notna(x) and '$' in str(x) else x
        )


        second_largest_df["file_name"] = file_name
        

        second_largest_df = second_largest_df.rename(columns={"Your Calling Plan": "Plan", "Data Usage (GB)": "Data Usage", "User Name": "Username", "Bill Cycle Date":"Bill Date"}, errors='ignore')
        bill_date = second_largest_df["Bill Date"].iloc[0]
        formatted_bill_date = self.parse_bill_date(bill_date)
        second_largest_df["bill_day"] = formatted_bill_date.day
        second_largest_df["bill_month"] = formatted_bill_date.month
        second_largest_df["bill_year"] = formatted_bill_date.year
        return second_largest_df
    def parse_bill_date(self, date_str):
        try:
            return parser.parse(date_str, dayfirst=False)  # US-style month/day
        except Exception:
            raise ValueError(f"Date format not supported: {date_str}")
    def manage_plans(self, df):
        if df is None or df.empty:
            return

        df = df.copy()
        df["Bill Date"] = pd.to_datetime(df["Bill Date"], errors="coerce")

        # --- Update plans ---
        new_plans = df["Plan"].dropna().unique().tolist()
        for plan in new_plans:
            if plan not in self.all_plans:
                self.all_plans.append(plan)

        # --- Update plan_charges with latest Bill Date ---
        latest = (
            df.dropna(subset=["Plan", "Monthly Charges", "Bill Date"])
            .sort_values("Bill Date")
            .groupby("Plan")
            .last()
        )

        for plan, charge in latest["Monthly Charges"].to_dict().items():
            self.plan_charges[plan] = charge

    def extract_highest_usage(self, *dfs):
        # Filter out None or empty DataFrames
        dfs = [df for df in dfs if df is not None and not df.empty]

        # If all are empty, return empty DataFrame
        if not dfs:
            return pd.DataFrame()

        # Combine all non-empty dataframes
        combined = pd.concat(dfs, ignore_index=True)
        # Convert usage to numeric
        combined["_usage_numeric"] = (
            combined["Data Usage"]
            .apply(lambda x: str(x).replace("GB", "").strip() if pd.notna(x) else None)
            .astype(float)
        )

        combined["_usage_numeric"] = pd.to_numeric(
            combined["_usage_numeric"], errors="coerce"
        ).fillna(0)

        # Find row with max usage per Wireless Number
        idx = combined.groupby("Wireless Number")["_usage_numeric"].idxmax()

        # Select rows and drop helper column
        highest = combined.loc[idx].drop(columns="_usage_numeric").reset_index(drop=True)
        return highest
    
    def store_summary_data(self,df):
        df = df.rename(columns={
            "Account Number": "account_number",
            "Bill Date": "bill_date",
            "Wireless Number": "wireless_number",
            "Username": "username",
            "Data Roaming": "data_roaming",
            "Message Roaming": "message_roaming",
            "Voice Roaming": "voice_roaming",
            "Data Usage": "data_usage",
            "Message Usage": "message_usage",
            "Voice Plan Usage": "voice_plan_usage",
            "Total Charges": "total_charges",
            "Third Party Charges (includes Tax)": "third_party_charges",  # <-- not in your model yet
            "Taxes, Governmental Surcharges and Fees": "taxes_governmental_surcharges",
            "Surcharges and Other Charges and Credits": "other_charges_credits",
            "Total Surcharges and Other Charges and Credits":"other_charges_credits",
            "Equipment Charges": "equipment_charges",
            "Usage and Purchase Charges": "usage_purchase_charges",
            "Plan": "plan",
            "Monthly Charges": "monthly_charges",
        })


        cols_to_clean = [
            "data_usage",
            "monthly_charges",
            "usage_purchase_charges",
            "equipment_charges",
            "other_charges_credits",
            "taxes_governmental_surcharges",
            "third_party_charges",
            "total_charges"
        ]

        for col in cols_to_clean:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace("$", "", regex=False)

        

        model_fields = {f.name for f in SummaryData._meta.get_fields()}
        records = []
        for row in df.to_dict(orient="records"):
            filtered = {k: v for k, v in row.items() if k in model_fields}
            records.append(SummaryData(multiple_analysis=self.instance,**filtered))

        # bulk insert
        SummaryData.objects.bulk_create(records, ignore_conflicts=True)
        
    def process(self):
        print("process start")
        try:
            dfs = []
            for path in self.file_paths:
                df = self.get_dataframe(path=path).copy()
                if not df.empty:
                    dfs.append(df)
            if not dfs:
                return False, "No valid files processed", 1
            print("got dfs")
            orginal_dfs = dfs
            
            for df in dfs:
                self.store_summary_data(df=df)

            print("stored summary")
            
            accounts = [df["Account Number"].iloc[0] for df in dfs if "Account Number" in df.columns]
            if len(set(accounts)) > 1:
                return False, f"Account Number mismatch detected! Found values: {accounts}", 1

            self.account_number = accounts[0]

            for df in dfs:
                self.manage_plans(df)

            print("plans managed")

            
            # Extract highest usage
            df = self.extract_highest_usage(*dfs, *(None,) * (3 - len(dfs)))

            print("highest usg")
            
            # Build output filename based on available Bill Dates
            dates = "_".join(
                [
                    pd.to_datetime(df["Bill Date"].iloc[0]).strftime("%Y-%m-%d")
                    for df in dfs if "Bill Date" in df.columns and pd.notna(df["Bill Date"].iloc[0])
                ]
            )

            output_file = f"{self.account_number}_{dates}.xlsx"
            

            # Export + DB save
            final_data = self.export_to_excel(orginal_dfs, df, filename=output_file)

            print("exported")
            merged_df = final_data.merge(
                df[['Bill Date', 'Wireless Number', 'file_name']],
                left_on=['bill_date', 'wireless_number'],
                right_on=['Bill Date', 'Wireless Number'],
                how='left'
            )
            merged_df = merged_df.drop(columns=['Bill Date', 'Wireless Number'])
            self.add_data_to_db(merged_df)

            print('in db')

            return True, 'RDD processed successfully', 1

        except Exception as e:
            return False, str(e), 0

from bot import BotClass
class AnalysisBotView(APIView):
    permission_classes = [IsAuthenticated]

    connection = None
    schema = None

    
            
    def get(self,request,ChatType,pk,*args,**kwargs):
        if not pk:
            return Response({"message":"Key required!"},status=status.HTTP_400_BAD_REQUEST)
        
        chats = BotChats.objects.filter(S_analysisChat=pk) if ChatType == "single" else BotChats.objects.filter(M_analysisChat=pk)
        ser = ChatSerializer(chats, many=True)
        return Response({"data":ser.data},status=status.HTTP_200_OK)
        
    def post(self,request,ChatType,pk,*args,**kwargs):
        botObj = BotClass(bot_type="analysis")
        data = request.data
        query_type = data.get('file_type')
        if not pk:
            return Response({"message":"Key required!"},status=status.HTTP_400_BAD_REQUEST)
        # self.connection, self.schema = init_database(query_type=query_type)
        self.connection, self.schema = botObj.init_database(query_type=query_type)
        data = request.data
        question = data.get("prompt")
        chatHis=BotChats.objects.filter(M_analysisChat=pk).values("question", "response", "created_at")
        df = pd.DataFrame(list(chatHis))

        try:
            instance = BotChats.objects.create(
                user=request.user,
                question=question,
                M_analysisChat=MultipleFileUpload.objects.filter(id=pk).first(),
            )

            is_generated, sql_query = botObj.get_analysis_sql_from_gemini(question, self.schema, special_id=pk, chat_history=df)

            if not is_generated:
                instance.is_query_generated = False
                instance.response = "I need a bit more info to answer.\nCould you please elaborate more on your question."
                instance.save()
                return Response({"response":"Unable to answer the question!"},status=status.HTTP_200_OK)

            is_ran, result_df = botObj.run_query(conn=self.connection, sql=sql_query)
            
            response_text = botObj.make_human_response(question, result_df, db_schema=self.schema)
            allLines = response_text.split("\n")
            questions = [line.strip() for line in allLines if line.strip().endswith("?")]
            other_lines = "\n".join([line.strip() for line in allLines if line.strip() and not line.strip().endswith("?")])
            if is_ran:
                instance.is_query_generated = True
                instance.is_query_ran = True
                instance.response = other_lines
                instance.recommended_questions = questions
            else:
                instance.is_df_empty = True
            instance.save()   

            # saveuserlog(request.user, f"Chatbot query executed: {question} | Response: {response_text}")

            return Response(
                {"response": response_text},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": f"Error processing request: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    def delete(self,request,ChatType,pk,*args,**kwargs):
        try:
            chats = BotChats.objects.filter(S_analysisChat=pk) if ChatType == "single" else BotChats.objects.filter(M_analysisChat=pk)
            chats.delete()
            return Response({"message":"user analysis chat deleted!"},status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"message":"Internal Server Error!"},status=status.HTTP_400_BAD_REQUEST)


class ExcelAnalysis:
    def __init__(self, instance):
        self.instance = instance
    def process(self):
        pass
        
from .chatspdf import convert_chats_to_pdf
from .Background.savingspdf import create_savings_pdf
class GetChatPdfView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,pk,*args,**kwargs):
        if not pk:
            return Response({"message":"Key required!"},status=status.HTTP_400_BAD_REQUEST)
        try:
            chatHis=BotChats.objects.filter(M_analysisChat=pk).exclude(response="I couldn't find any information matching your request.").values("question", "response")
            df = pd.DataFrame(list(chatHis))
            if df.empty:
                return Response({"message":"No chat history found!"},status=status.HTTP_400_BAD_REQUEST)
            account_number = AnalysisData.objects.filter(multiple_analysis_id=pk).values_list("account_number", flat=True).distinct()[0]
            bill_dates = sorted(
                list(AnalysisData.objects.filter(multiple_analysis_id=pk).values('bill_month', 'bill_year').distinct()),
                key=lambda x: (x['bill_year'], x['bill_month'])
            )
            formatted_dates = [
                f"{calendar.month_name[item['bill_month']]} {item['bill_year']}"
                for item in bill_dates
            ]
            pdf = convert_chats_to_pdf(df,account_number, formatted_dates)
            filename = f"chat_history_{account_number}_{'_'.join(formatted_dates).replace(' ', '_')}.pdf"
            if not pdf:
                return Response({"message":"Error generating PDF!"},status=status.HTTP_400_BAD_REQUEST)
            # return PDF directly as response with status 200
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response
        except Exception as e:
            print(e)
            return Response({"message":"Internal Server Error!"},status=status.HTTP_400_BAD_REQUEST)
import calendar
class GetSavingsPdfView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request,pk,*args,**kwargs):
        if not pk:
            return Response({"message":"Key required!"},status=status.HTTP_400_BAD_REQUEST)
        try:
            savings=AnalysisData.objects.filter(multiple_analysis=pk).exclude(recommended_plan="").values("user_name", "wireless_number", "current_plan", "current_plan_charges", "current_plan_usage", "recommended_plan", "recommended_plan_charges", "recommended_plan_savings")
            df = pd.DataFrame(list(savings))
            if df.empty:
                print("no df found!")
                return Response({"message":"No chat history found!"},status=status.HTTP_400_BAD_REQUEST)
            # get the account number and differnt bill dates in list format from AnalysisData table for the given analysis id
            account_number = AnalysisData.objects.filter(multiple_analysis_id=pk).values_list("account_number", flat=True).distinct()[0]
            bill_dates = sorted(
                list(AnalysisData.objects.filter(multiple_analysis_id=pk).values('bill_month', 'bill_year').distinct()),
                key=lambda x: (x['bill_year'], x['bill_month'])
            )
            formatted_dates = [
                f"{calendar.month_name[item['bill_month']]} {item['bill_year']}"
                for item in bill_dates
            ]
            # prepend accountsavings_report
            pdf = create_savings_pdf(df, account_number, formatted_dates)
            dates = "_".join(formatted_dates).replace(" ", "_")
            filename = f"savings_report_{account_number}_{dates}.pdf"

            if not pdf:
                return Response({"message": "Error generating PDF!"}, status=status.HTTP_400_BAD_REQUEST)

            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response


        except Exception as e:
            print(e)
            return Response({"message":"Internal Server Error!"},status=status.HTTP_400_BAD_REQUEST)
        
        
        





# -------- Helpers
def _qs_for_file(file_id):
    return AnalysisData.objects.filter(multiple_analysis_id=file_id)

def _expense_after_expr():
    return Case(
        When(recommended_plan_charges__isnull=False, then=F('recommended_plan_charges')),
        default=F('current_plan_charges'),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )


from decimal import Decimal
from django.db.models import Sum, Count, F, Case, When, DecimalField, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated  

DECIMAL_OUT = DecimalField(max_digits=12, decimal_places=2)
DEC0 = Value(Decimal("0.00"), output_field=DECIMAL_OUT)

def safe_int(v):
    try:
        return int(str(v).strip().rstrip("/"))
    except Exception:
        return None

class AnalysisDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            file_id = safe_int(request.query_params.get("file_id"))
            if not file_id:
                return Response({"error": "file_id required"}, status=400)

            qs = _qs_for_file(file_id)

            total_spend = qs.aggregate(
                v=Coalesce(Sum('current_plan_charges', output_field=DECIMAL_OUT), DEC0)
            )['v'] or Decimal("0.00")

            monthly_savings = qs.aggregate(
                v=Coalesce(Sum('recommended_plan_savings', output_field=DECIMAL_OUT), DEC0)
            )['v'] or Decimal("0.00")

            annualized_savings = monthly_savings * 12  

            zero_use_lines = qs.filter(data_usage_range='zero_usage') \
                            .values('wireless_number').distinct().count()

            before_total = total_spend

            after_total = qs.aggregate(
                v=Coalesce(Sum(_expense_after_expr(), output_field=DECIMAL_OUT), DEC0)
            )['v'] or Decimal("0.00")

            by_bucket = (
                qs.values('data_usage_range')
                .annotate(
                    lines=Count('id'),
                    savings=Coalesce(Sum('recommended_plan_savings', output_field=DECIMAL_OUT), DEC0),
                    spend=Coalesce(Sum('current_plan_charges', output_field=DECIMAL_OUT), DEC0),
                )
                .order_by('-savings')
            )
            total_savings_for_share = float(sum(row['savings'] for row in by_bucket) or Decimal("1.00"))
            savings_breakdown = [
                {
                    "bucket": row["data_usage_range"],
                    "lines": row["lines"],
                    "savings": float(row["savings"]),
                    "share_pct": round(100.0 * float(row["savings"]) / total_savings_for_share, 2),
                }
                for row in by_bucket
            ]

            series = (
                qs.values('bill_year', 'bill_month')
                .annotate(
                    spend=Coalesce(Sum('current_plan_charges', output_field=DECIMAL_OUT), DEC0),
                    savings=Coalesce(Sum('recommended_plan_savings', output_field=DECIMAL_OUT), DEC0),
                )
                .order_by('bill_year', 'bill_month')
            )
            savings_over_time = [
                {
                    "label": f"{row['bill_year']}-{int(row['bill_month']):02d}",
                    "spend": float(row["spend"]),
                    "savings": float(row["savings"]),
                }
                for row in series
            ]

            payload = {
                "file_id": file_id,
                "kpis": {
                    "total_spend": float(total_spend),
                    "zero_use_lines": int(zero_use_lines),
                    "monthly_savings": float(monthly_savings),
                    "annualized_savings": float(annualized_savings),
                    "expense_reduction": {
                        "before": float(before_total),
                        "after": float(after_total),
                        "delta": float(before_total - after_total),
                    },
                },
                "breakdown": savings_breakdown,
                "savings_over_time": savings_over_time,
            }

            compare_file_id = safe_int(request.query_params.get("compare_file_id"))
            if compare_file_id:
                qs2 = _qs_for_file(compare_file_id)
                before2 = qs2.aggregate(
                    v=Coalesce(Sum('current_plan_charges', output_field=DECIMAL_OUT), DEC0)
                )['v'] or Decimal("0.00")

                after2  = qs2.aggregate(
                    v=Coalesce(Sum(_expense_after_expr(), output_field=DECIMAL_OUT), DEC0)
                )['v'] or Decimal("0.00")

                payload["comparison"] = {
                    "compare_file_id": compare_file_id,
                    "expense_reduction": {
                        "before": float(before2),
                        "after": float(after2),
                        "delta": float(before2 - after2),
                    }
                }

            return Response(payload)


        except Exception as e:
            print("DASHBOARD ERROR")
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)

class AnalysisLinesPagination(PageNumberPagination):
    page_size = 25
    max_page_size = 200

class AnalysisLinesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            file_id = safe_int(request.query_params.get("file_id"))
            if not file_id:
                return Response({"error": "file_id required"}, status=400)

            qs = _qs_for_file(file_id)
            print("DEBUG lines:", qs.count())

            qs = qs.values(
                'wireless_number', 'user_name',
                'current_plan', 'current_plan_charges',
                'recommended_plan', 'recommended_plan_charges',
                'recommended_plan_savings', 'data_usage_range',
                'bill_year', 'bill_month', 'bill_day'
            ).order_by('user_name', 'wireless_number')

            paginator = AnalysisLinesPagination()
            page = paginator.paginate_queryset(qs, request)
            return paginator.get_paginated_response(page)

        except Exception as e:
            print("LINES ERROR")
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
        
        
        
        
        
# Common Dashboard        


# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from collections import defaultdict
from decimal import Decimal
from datetime import date
from collections import namedtuple

from OnBoard.Ban.models import BaseDataTable
from .utils import parse_money, parse_date
from .filters import apply_common_filters
from Dashboard.ModelsByPage.Req import Requests
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta


from datetime import datetime, date
from decimal import Decimal
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response

# if you already have parse_money, keep using it
# from .utils import parse_money

# robust but simple date parser for your formats
def try_parse_due_date(raw):
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None

    # handle the special marker
    if s.lower() == "past":
        return "PAST"  # sentinel we’ll treat as overdue

    # supported formats in your screenshot
    fmts = (
        "%m/%d/%y",   # 02/14/24 or 9/11/24
        "%m/%d/%Y",   # 02/14/2024
        "%b %d %Y",   # Jul 24 2023 / May 24 2025
        "%b %d %y",   # Jul 24 23
        "%B %d %Y",   # July 24 2023
        "%B %d %y",   # July 24 23
    )
    for fmt in fmts:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None  # unparseable stays ignored

class BillSummaryView(APIView):
    def get(self, request):
        qs = apply_common_filters(BaseDataTable.objects.exclude(viewuploaded=None, viewpapered=None), request)
        today = date.today()

        total_bills = 0
        total_charges_sum = Decimal("0")
        total_amount_due_sum = Decimal("0")
        due_soon = 0
        overdue = 0

        for b in qs.iterator():
            total_bills += 1
            total_charges_sum += parse_money(b.net_amount)
            total_amount_due_sum += parse_money(b.Total_Amount_Due)

            parsed = try_parse_due_date(b.date_due)

            if parsed == "PAST":
                # explicit marker → overdue
                overdue += 1
                continue

            if isinstance(parsed, date):
                if parsed < today:
                    overdue += 1
                else:
                    delta = (parsed - today).days
                    if 0 <= delta <= 7:
                        due_soon += 1
            # else: None/unparseable → ignore for overdue/soon

        return Response({
            "total_bills": total_bills,
            "total_charges_sum": float(total_charges_sum),
            "total_amount_due_sum": float(total_amount_due_sum),
            "overdue_count": overdue,
            "due_soon_count": due_soon,
        })



class BillExtremesView(APIView):
    def get(self, request):
        """
        Returns highest and lowest total_charges for the currently filtered slice,
        with no duplication between the two lists—even when the dataset is tiny.
        """
        # 1) Base queryset: uploaded bills only + common filters
        qs = apply_common_filters(
            BaseDataTable.objects.filter(banOnboarded__isnull=True, banUploaded__isnull=True),
            request
        )

        print("filtered queries==", qs)

        # 2) Optional date window passed via apply_common_filters
        date_from = getattr(request, "_analytics_date_from", None)
        date_to = getattr(request, "_analytics_date_to", None)

        # 3) Limit handling
        try:
            limit = int(request.query_params.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        limit = max(1, min(limit, 50))  # 1..50

        # 4) Collect items (parse numbers/dates safely)
        items = []
        for b in qs.iterator():
            bdate = parse_date(b.bill_date) or parse_date(b.BillingDate)
            if date_from and (not bdate or bdate < date_from):
                continue
            if date_to and (not bdate or bdate > date_to):
                continue

            items.append({
                "id": b.id,
                "company": b.company,
                "sub_company": b.sub_company,
                "vendor": b.vendor,
                "invoicenumber": b.invoicenumber,
                "accountnumber": b.accountnumber,
                "bill_date": b.bill_date,
                "date_due": b.date_due,
                "total_charges_num": parse_money(b.total_charges),  # Decimal
            })

        # 5) Sort by numeric total_charges
        items.sort(key=lambda x: x["total_charges_num"])

        # 6) Build non-overlapping extremes
        n = len(items)
        if n == 0:
            lowest, highest = [], []
        elif n == 1:
            # one bill → show it once, mark as high (low would be redundant)
            lowest, highest = [], items
        elif n == 2:
            # two bills → one low, one high (no duplication)
            lowest, highest = [items[0]], [items[1]]
        else:
            # pick up to `limit` from each side, with no overlap
            half = min(limit, n // 2) or 1
            lowest = items[:half]
            highest = items[-half:]

            # safety: ensure disjoint sets by id
            low_ids = {i["id"] for i in lowest}
            highest = [i for i in highest if i["id"] not in low_ids]

        # 7) JSON-safe numbers
        for arr in (lowest, highest):
            for it in arr:
                it["total_charges_num"] = float(it["total_charges_num"])

        # 8) Echo active filters for transparency/debug
        ctx = {
            "company": request.query_params.get("company"),
            "sub_company": request.query_params.get("sub_company"),
            "vendor": request.query_params.get("vendor"),
            "year": request.query_params.get("year"),
            "month": request.query_params.get("month"),
            "date_from": request.query_params.get("date_from"),
            "date_to": request.query_params.get("date_to"),
            "uploaded_only": True,
            "limit": limit,
            "total_considered": n,
        }

        return Response({
            "highest": highest,
            "lowest": lowest,
            "filters": ctx,
        })
class BillTotalsView(APIView):
    def get(self, request):
        dim = request.query_params.get("by", "vendor")
        if dim not in ("vendor", "company", "sub_company"):
            dim = "vendor"

        qs = apply_common_filters(BaseDataTable.objects.all(), request)
        bucket = defaultdict(lambda: {"sum": Decimal("0"), "count": 0, "currency": None})

        for b in qs.iterator():
            key = getattr(b, dim) or "Unknown"
            bucket[key]["sum"] += parse_money(b.total_charges)
            bucket[key]["count"] += 1
            bucket[key]["currency"] = b.BillingCurrency

        out = [
            {"label": k, "count": v["count"], "sum": float(v["sum"]), "currency": v["currency"]}
            for k, v in bucket.items()
        ]
        out.sort(key=lambda x: x["sum"], reverse=True)
        return Response({"dimension": dim, "rows": out})


class BillStatusBreakdownView(APIView):
    def get(self, request):
        qs = apply_common_filters(BaseDataTable.objects.exclude(viewuploaded=None, viewpapered=None), request)
        batch = defaultdict(int)
        ban = defaultdict(int)

        for b in qs.iterator():
            batch[b.batch_approved or "Pending"] += 1
            ban[b.banstatus or "Unknown"] += 1

        return Response({
            "batch_approved": [{"status": k, "count": v} for k, v in batch.items()],
            "banstatus": [{"status": k, "count": v} for k, v in ban.items()],
        })


class BillTimeSeriesView(APIView):
    def get(self, request):
        dim = request.query_params.get("by", "total_charges")
        if dim not in ("total_charges", "Total_Amount_Due"):
            dim = "total_charges"

        qs = apply_common_filters(BaseDataTable.objects.all(), request)
        series = defaultdict(lambda: Decimal("0"))
        for b in qs.iterator():
            y, m = str(b.year or ""), str(b.month or "")
            if not (y and m):
                continue
            key = f"{y}-{m.zfill(2)}"
            val = getattr(b, dim, "")
            series[key] += parse_money(val)

        out = [{"period": k, "sum": float(v)} for k, v in sorted(series.items())]
        return Response({"metric": dim, "points": out})




class RequestSummaryView(APIView):
    def _get_model_vise(self, request, query_table):
        params = request.query_params
        qs = query_table.objects.select_related("vendor", "organization").all()
        vendor = params.get("vendor")
        org = params.get("organization")
        request_type = params.get("request_type")


        userOrg = request.user.organization
        if userOrg:
            qs = qs.filter(organization=userOrg)
        elif org:
            qs = qs.filter(organization__Organization_name__iexact=org)
        if vendor:
            qs = qs.filter(vendor__name__iexact=vendor)
        if request_type:
            qs = qs.filter(request_type__iexact=request_type)

        total = qs.count()
        pending = qs.filter(status__iexact="Pending").count()
        approved = qs.filter(status__iexact="Approved").count()
        completed = qs.filter(authority_status__iexact="Completed").count()
        cancelled = qs.filter(status__iexact="Rejected").count()

        last_7_days = qs.filter(created__gte=timezone.now() - timedelta(days=7)).count()
        last_30_days = qs.filter(created__gte=timezone.now() - timedelta(days=30)).count()

        # --- status breakdown for charts ---
        status_order = ["Pending", "Approved", "Completed", "Cancelled"]
        raw = (
            qs.exclude(status__isnull=True)
              .exclude(status__exact="")
              .values("authority_status")
              .annotate(count=Count("id"))
        )
        by_status = {row["authority_status"].strip(): row["count"] for row in raw if row["authority_status"]}

        request_status = [
            {"status": s, "count": by_status.get(s, 0)}
            for s in status_order
        ]

        # request type + vendor breakdowns (unchanged from earlier fix)
        type_breakdown = (
            qs.values("request_type").annotate(count=Count("id")).order_by("-count")[:8]
        )
        vendor_breakdown = (
            qs.values("vendor__name").annotate(count=Count("id")).order_by("-count")[:8]
        )
        return {
            "total_requests": total,
            "pending_requests": pending,
            "approved_requests": approved,
            "completed_requests": completed,
            "cancelled_requests": cancelled,
            "last_7_days": last_7_days,
            "last_30_days": last_30_days,
            "type_breakdown": [
                {"type": t["request_type"], "count": t["count"]} for t in type_breakdown
            ],
            "vendor_breakdown": [
                {"vendor": v["vendor__name"], "count": v["count"]}
                for v in vendor_breakdown
            ],
            # 👇 this is what your chart should bind to
            "request_status": request_status,
        }
    def get(self, request):
        return Response({"request_management":self._get_model_vise(request, Requests), "accessories_requests":self._get_model_vise(request, AccessoriesRequest), "device_upgrade_requests":self._get_model_vise(request, upgrade_device_request)})



from django.db.models import Sum, Count, F
from .filters import apply_ba_filters
from View.models import BillAnalysisData  # adjust import to your app path



USAGE_LABELS = {
    "zero_usage": "Zero-Use",
    "less_than_5_gb": "Less Than 5 GB",
    "between_5_and_15_gb": "Between 5–15 GB",
    "more_than_15_gb": "More Than 15 GB",
    "NA_not_unlimited": "N/A (Not Unlimited)",
    "NA_unlimited": "N/A (Unlimited)",
}

class BAUsageSummaryView(APIView):
    def get(self, request):
        qs = apply_ba_filters(BillAnalysisData.objects.all(), request)

        raw = qs.values("data_usage_range").annotate(count=Count("id"))
        usage = [
            {"key": r["data_usage_range"],
             "range": USAGE_LABELS.get(r["data_usage_range"], r["data_usage_range"] or "NA"),
             "count": r["count"]}
            for r in raw
        ]

        total_lines = qs.count()
        zero_use = qs.filter(data_usage_range="zero_usage").count()

        # downgrade candidates ~= low / moderate usage lines
        downgrade_candidates = qs.filter(
            data_usage_range__in=["less_than_5_gb","between_5_and_15_gb"]
        ).count()

        return Response({
            "total_lines": total_lines,
            "zero_use": zero_use,
            "downgrade_candidates": downgrade_candidates,
            "usage": usage,
        })

class BAOptimizationSummaryView(APIView):
    def get(self, request):
        qs = apply_ba_filters(BillAnalysisData.objects.filter(is_plan_recommended=True), request)
        agg = qs.aggregate(
            recommended_lines=Count("id"),
            potential_savings=Sum("recommended_plan_savings"),
        )
        total = int(agg["recommended_lines"] or 0)
        monthly_savings = float(agg["potential_savings"] or 0)
        return Response({
            "recommended_lines": total,
            "monthly_savings": monthly_savings,
            "annualized_savings": monthly_savings * 12.0,
            "avg_savings_per_line": (monthly_savings / total) if total else 0.0,
        })

class BATopSavingsView(APIView):
    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 10))
        except Exception:
            limit = 10
        limit = max(1, min(limit, 50))
        qs = apply_ba_filters(
            BillAnalysisData.objects.filter(is_plan_recommended=True), request
        ).order_by(F("recommended_plan_savings").desc(nulls_last=True))[:limit]

        rows = [{
            "wireless_number": r.wireless_number,
            "user_name": r.user_name,
            "vendor": r.vendor,
            "account_number": r.account_number,
            "current_plan": r.current_plan,
            "current_plan_charges": float(r.current_plan_charges or 0),
            "recommended_plan": r.recommended_plan,
            "recommended_plan_charges": float(r.recommended_plan_charges or 0),
            "recommended_plan_savings": float(r.recommended_plan_savings or 0),
            "data_usage_range": USAGE_LABELS.get(r.data_usage_range, r.data_usage_range or "NA"),
        } for r in qs]
        return Response({"rows": rows})

class BASavingsTimeSeriesView(APIView):
    """
    Potential savings by bill month (pairs to your spend time series).
    """
    def get(self, request):
        qs = apply_ba_filters(
            BillAnalysisData.objects.filter(is_plan_recommended=True),
            request,
        )
        points = (
            qs.values("bill_year","bill_month")
              .annotate(sum=Sum("recommended_plan_savings"))
        )
        # produce 'YYYY-MM' keys sorted
        def key(p):
            y = int(p["bill_year"] or 0); m = int(p["bill_month"] or 0)
            return f"{y}-{str(m).zfill(2)}"
        out = [{"period": key(p), "sum": float(p["sum"] or 0)} for p in points]
        out.sort(key=lambda x: x["period"])
        return Response({"metric":"recommended_plan_savings","points": out})





# User Dashboard




# analytics/views.py
import json
from decimal import Decimal
from django.db.models import Count, Q
from django.db.models.functions import Lower
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from OnBoard.Ban.models import BaselineDataTable
from Dashboard.ModelsByPage.Req import Requests, TrackingInfo, upgrade_device_request, AccessoriesRequest


def _parse_category_object(value):
    """
    Accepts dict or JSON string; returns dict[str, dict[str, Decimal/float]].
    Silently falls back to {} if invalid.
    """
    if not value:
        return {}
    try:
      # if already dict-ish
      if isinstance(value, dict):
          return value
      # JSONField sometimes stores strings in DB; try parse
      return json.loads(value)
    except Exception:
      return {}


def _category_totals(cat_obj_dict):
    """
    cat_obj_dict = {"CATEGORY": {"sub": num, ...}, ...}
    -> [{"label": "CATEGORY", "sum": <float>}]
    """
    out = []
    for cat, sub in (cat_obj_dict or {}).items():
        total = 0.0
        if isinstance(sub, dict):
            for _, v in sub.items():
                try:
                    total += float(v or 0)
                except Exception:
                    pass
        out.append({"label": cat, "sum": total})
    # highest first for nicer charts
    out.sort(key=lambda x: x["sum"], reverse=True)
    return out


class BaselineDetailView(APIView):
    """
    Returns a single BaselineDataTable record for the required 5 filters.
    Enforces that viewuploaded_id and viewpapered_id are NOT NULL.
    """

    REQUIRED_KEYS = ("company", "sub_company", "vendor", "account_number", "wireless_number")

    def get(self, request):
        # 1) validate required params
        missing = [k for k in self.REQUIRED_KEYS if not (request.query_params.get(k) or "").strip()]
        if missing:
            return Response(
                {"detail": f"Missing required query params: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        company = request.query_params.get("company").strip()
        sub_company = request.query_params.get("sub_company").strip()
        vendor = request.query_params.get("vendor").strip()
        account_number = request.query_params.get("account_number").strip()
        wireless_number = request.query_params.get("wireless_number").strip()

        # 2) base queryset with required documents present
        qs = BaselineDataTable.objects.filter(
    Q(banOnboarded__isnull=False) | Q(banUploaded__isnull=False),
    company__icontains=company,
    sub_company__icontains=sub_company,
    vendor__icontains=vendor,
    account_number__icontains=account_number,
    Wireless_number__icontains=wireless_number,
)
        # 3) fetch the single record
        if not qs.exists():
            return Response({"detail": "No matching baseline record found with required docs."},
                            status=status.HTTP_404_NOT_FOUND)

        if qs.count() > 1:
            # If data integrity ever breaks, let the caller know
            return Response({"detail": "Multiple records found for the given filters; expected exactly one."},
                            status=status.HTTP_409_CONFLICT)

        obj = qs.first()

        # 4) parse category_object and compute totals (backend does the heavy lift)
        cat_obj = _parse_category_object(obj.category_object)
        cat_totals = _category_totals(cat_obj)

        # 5) shape the response (only fields needed by frontend)
        record = {
            "id": obj.id,
            "company": obj.company,
            "sub_company": obj.sub_company,
            "vendor": obj.vendor,
            "account_number": obj.account_number,
            "Wireless_number": obj.Wireless_number,
            "user_name": obj.user_name,
            "plans": obj.plans,
            "plan_type": obj.plan_type,
            "data_allotment": obj.data_allotment,
            "plan_fee": obj.plan_fee,
            "smartphone": obj.smartphone,
            "tablet_computer": obj.tablet_computer,
            "mifi": obj.mifi,
            "wearables": obj.wearables,
            "cost_center": obj.cost_center,
            "VendorNumber": obj.VendorNumber,
            "paymentstatus": obj.paymentstatus,
            "bill_date": obj.bill_date,
            "banOnboarded_id": getattr(obj, "banOnboarded_id", None),
            "banUploaded_id": getattr(obj, "banUploaded_id", None),
            "category_object": cat_obj,     # normalized object
        }

        return Response(
            {
                "record": record,
                "category_totals": cat_totals,
            },
            status=status.HTTP_200_OK,
        )


class BaselineAnalyticsView(APIView):
    """
    (Optional) Keep your previous summary endpoint if other screens still use it.
    """
    def get(self, request):
        company = request.query_params.get('company')
        sub_company = request.query_params.get('sub_company')
        vendor = request.query_params.get('vendor')
        account_number = request.query_params.get('account_number')
        wireless_number = request.query_params.get('wireless_number')

        qs = BaselineDataTable.objects.all()

        if company:
            qs = qs.filter(company__icontains=company)
        if sub_company:
            qs = qs.filter(sub_company__icontains=sub_company)
        if vendor:
            qs = qs.filter(vendor__icontains=vendor)
        if account_number:
            qs = qs.filter(account_number__icontains=account_number)
        if wireless_number:
            qs = qs.filter(Wireless_number__icontains=wireless_number)

        total_records = qs.count()
        unique_accounts = qs.values_list("account_number", flat=True).distinct().count()
        unique_wireless = qs.values_list("Wireless_number", flat=True).distinct().count()
        unique_vendors = qs.values_list("vendor", flat=True).distinct().count()

        by_vendor = qs.values(label=Lower("vendor")).annotate(count=Count("id")).order_by("-count")
        by_company = qs.values(label=Lower("company")).annotate(count=Count("id")).order_by("-count")
        by_subcompany = qs.values(label=Lower("sub_company")).annotate(count=Count("id")).order_by("-count")

        return Response(
            {
                "totals": {
                    "records": total_records,
                    "uniqueAccounts": unique_accounts,
                    "uniqueWireless": unique_wireless,
                    "vendors": unique_vendors,
                },
                "breakdowns": {
                    "byVendor": list(by_vendor),
                    "byCompany": list(by_company),
                    "bySubCompany": list(by_subcompany),
                },
            },
            status=status.HTTP_200_OK,
        )


class RequestsAnalyticsView(APIView):
    def _request_management(self, params, query_table):
        requester_id = params.get("requester_id")
        qs = query_table.objects.all()
        if requester_id:
            if has_field(query_table, "raised_by"):
                qs = qs.filter(raised_by_id=requester_id)
            elif has_field(query_table, "requester"):
                qs = qs.filter(requester_id=requester_id)
            else:qs=qs
        total_requests = qs.count()
        pending = qs.filter(authority_status__iexact="Pending").count()
        completed = qs.filter(authority_status__iexact="Completed").count()
        rejected = qs.filter(status__iexact="Rejected").count()

        by_type = (
            qs.values(label=Lower("request_type"))
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        by_status = (
            qs.values(label=Lower("authority_status"))
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        recent = (
            qs.order_by("-request_date")
            .values("id", "request_type", "authority_status", "user_name", "request_date")[:10]
        )
        return {
                "totals": {
                    "requests": total_requests,
                    "pending": pending,
                    "completed": completed,
                    "rejected":rejected
                },
                "byType": list(by_type),
                "byStatus": list(by_status),
                "recent": list(recent),
            },
    def get(self, request):
        return Response({"request_management":self._request_management(request.query_params,query_table=Requests),"accessories_management": self._request_management(request.query_params,AccessoriesRequest), "upgrade_device":self._request_management(request.query_params,upgrade_device_request)},status=status.HTTP_200_OK)


class TrackingAnalyticsView(APIView):
    """
    Tracking overview; minor hardening so empty strings are treated as unknown status.
    """
    def get(self, request):
        qs = TrackingInfo.objects.all()

        total_shipments = qs.count()
        vendors = qs.values_list("shipment_vendor", flat=True).distinct().count()
        device_status_known = qs.filter(~Q(device_status__isnull=True) & ~Q(device_status="")).count()

        by_vendor = qs.values(label=Lower("shipment_vendor")).annotate(count=Count("id")).order_by("-count")
        by_status = qs.values(label=Lower("device_status")).annotate(count=Count("id")).order_by("-count")

        recent = qs.order_by("-updated").values(
            "id", "shipment_vendor", "tracking_id", "device_status", "updated"
        )[:10]

        return Response(
            {
                "totals": {
                    "shipments": total_shipments,
                    "deviceStatusKnown": device_status_known,
                    "vendors": vendors,
                },
                "byShipmentVendor": list(by_vendor),
                "byDeviceStatus": list(by_status),
                "recent": list(recent),
            },
            status=status.HTTP_200_OK,
        )

from rest_framework.decorators import api_view, permission_classes


from django.forms.models import model_to_dict

@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def get_unapproved_bills(request, org, *args, **kwargs):
    unapproved_bills = BaseDataTable.objects.exclude(viewuploaded=None).filter(viewpapered=None).filter(sub_company=org).exclude(batch_approved="Approved")
    response = [model_to_dict(item, fields=["id", "bill_date", "accountnumber", "invoicenumber", "sub_company", "net_amount", "vendor"]) for item in unapproved_bills]
    return Response({"count":len(unapproved_bills), "data":response},status=status.HTTP_200_OK)

from OnBoard.Ban.models import UploadBAN, OnboardBan, BaseDataTable, BaselineDataTable
from OnBoard.Organization.models import Organizations
@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def get_ban_onboard_status(request, org, *args, **kwargs):
    data = request.GET
    upload_type = data.get("upload_type")
    id = data.get("id")
    if not upload_type or id:
        return Response({"message":"Insufficient data!"},status=status.HTTP_400_BAD_REQUEST)
    
    if upload_type == "direct":
        obj = OnboardBan.objects.filter(id=id).first()
    elif upload_type == "manual":
        obj = UploadBAN.objects.filter(id=id).first()
    else:
        obj = None
    if not obj:
        return Response({"message":"data not found!"},status=status.HTTP_400_BAD_REQUEST)
    
from OnBoard.Ban.models import UploadBAN, OnboardBan, BaseDataTable, BaselineDataTable, UniquePdfDataTable

@api_view(["GET"])
# @permission_classes([IsAuthenticated])
def get_ban_onboard_status(request, org, *args, **kwargs):
    # Get organization
    organization = Organizations.objects.filter(
        Organization_name=org
    ).first()

    if not organization:
        return Response(
            {"message": "Organization not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get all BANs (manual + direct)
    all_manual = UploadBAN.objects.filter(organization=organization)
    all_direct = OnboardBan.objects.filter(organization=organization)
    all_bans = list(
        set(
            list(all_manual.values_list("account_number", flat=True))
            + list(all_direct.values_list("account_number", flat=True))
        )
    )

    if not all_bans:
        return Response(
            {"message": "No BANs found for this organization.", "data": []},
            status=status.HTTP_200_OK
        )

    # Fetch onboarded (BaseDataTable) and baseline (UniquePdfDataTable) data
    base_objs = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(accountnumber__in=all_bans)
    baseline_objs = UniquePdfDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(account_number__in=all_bans)

    # Map account_number → vendor
    vendor_map = {
        obj.accountnumber: obj.vendor for obj in base_objs
    }

    # Create lookup sets
    onboarded_accounts = set(base_objs.values_list("accountnumber", flat=True))

    # Baseline validation per BAN
    baseline_status = {}
    for ban in all_bans:
        ban_records = baseline_objs.filter(account_number=ban)
        if not ban_records.exists():
            baseline_status[ban] = False
            continue

        # Check if all category_objects are filled
        all_valid = all(
            record.category_object not in [None, "", {}, []]
            for record in ban_records
        )
        baseline_status[ban] = all_valid

    # Build result
    result = []
    for ban in all_bans:
        result.append({
            "account_number": ban,
            "vendor": vendor_map.get(ban, None),  # ✅ Added vendor info
            "is_onboarded": ban in onboarded_accounts,
            "is_baseline_created": baseline_status.get(ban, False),
        })

    return Response(result, status=status.HTTP_200_OK)