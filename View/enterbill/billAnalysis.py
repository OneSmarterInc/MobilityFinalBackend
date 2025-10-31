import logging
import pdfplumber
from AnalysisScripts.VerizonNew import VerizonClass
from AnalysisScripts.AttNew import AttClass
from AnalysisScripts.TMobile1New import Tmobile1Class
from AnalysisScripts.TMobile2New import Tmobile2Class
import pandas as pd
import io
import json
import os
from django.conf import settings
from ..models import ProcessedWorkbook
from django.core.files import File
logging.basicConfig(level=logging.INFO)
from baselineTag import object_tagging
from addon import get_cat_obj_total
from OnBoard.Company.models import Company
from authenticate.models import PortalUser
from django.utils import timezone
from View.models import BillSummaryData, BillAnalysisData
from django.db import transaction
from addon import extract_data_from_zip


from dateutil import parser
import re
import time

class BillAnalysis:
    # sleep for 10 seconds to simulate a long-running task
    time.sleep(2)
    def __init__(self, instance,btype, buffer_data):
        if not instance or not instance.pk:
            raise ValueError("Invalid instance provided for BillAnalysis")
        self.instance = instance
        self.buffer_data = json.loads(buffer_data) if isinstance(buffer_data, str) else buffer_data
        self.filepath = self.buffer_data.get('pdf_path') if self.buffer_data.get('pdf_path') else self.buffer_data.get('file_path')
        self.company_name = self.buffer_data.get('company_name')
        self.vendor_name = self.buffer_data.get('vendor_name')

        self.file_name = self.get_filename(self.filepath)

        self.account_number = None
        self.bill_date = None
        self.bill_day = None
        self.bill_month = None
        self.bill_year = None
        self.all_plans = []
        self.plan_charges = {}
        self.t_mobile_type = btype if btype else 0

    def get_filename(self,path):
        print("get filename")
        file_path = path.split("/")[-1]        
        name, ext = file_path.rsplit(".", 1)     
        ext = "." + ext                          

        if "_" in name:
            name = name.rsplit("_", 1)[0]

        return f"{name}{ext}"

    def process_zip_file_separately(self, path):
        print("def process_zip_file_separately")
        try:
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

            second_largest_df["file_name"] = self.get_filename(path=path)

            second_largest_df = second_largest_df.rename(columns={"Your Calling Plan": "Plan", "Data Usage (GB)": "Data Usage", "User Name": "Username", "Bill Cycle Date":"Bill Date"}, errors='ignore')
            return second_largest_df
        except Exception as e:
            print(f"Error processing file: {e}")
            return pd.DataFrame()
    def process_pdf_file_separately(self,path, Script):
        print("def process_pdf_file_separately")

        try:
            scripter = Script(path)
            basic_data, line_items, processing_time = scripter.extract_all()
            self.account_number = basic_data.get("Account Number")
            line_items["Monthly Charges"] = line_items["Monthly Charges"].apply(lambda x: f"${x}" if isinstance(x, (int, float)) else x)
            line_items.insert(0, "Account Number", basic_data.get("Account Number"))
            bill_date = basic_data.get("Bill Date")
            line_items.insert(1, "Bill Date",bill_date)
            return line_items
        except Exception as e:
            print(f"Error processing file: {e}")
            return pd.DataFrame()
        
    def parse_bill_date(self, date_str):
        try:
            return parser.parse(date_str, dayfirst=False)  # US-style month/day
        except Exception:
            raise ValueError(f"Date format not supported: {date_str}")
        
    def manage_plans(self, df):
        print("def manage_plans")
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
    
    def safe_float(self, value, default=0.0):
        try:
            if pd.isna(value):
                return default
            value_str = str(value).strip().upper()
            if value_str in ("NA", "N/A", "", "NONE", "NAN"):
                return default
            return float(value_str.replace("$", "").replace("GB", "").strip())
        except Exception:
            return default

    def insert_summary_and_analytics(self, df):
        print("def insert_summary_and_analytics")

        cols = {
            "Third Party Charges (includes Tax)":"third_party_charges",
            "Taxes, Governmental Surcharges and Fees":"taxes_governmental_surcharges",
            "Surcharges and Other Charges and Credits":"other_charges_credits",
            "Usage and Purchase Charges":"usage_purchase_charges",
            "Equipment Charges":"equipment_charges",
            "Taxes and Surcharges": "taxes_governmental_surcharges",
            "Third Party Services":"third_party_charges",
            "Usage Charges": "usage_purchase_charges", 
            "Credits & Adjustments": "other_charges_credits",
            "Government fees and taxes": "taxes_governmental_surcharges",
            "Company fees and surcharges":"other_charges_credits",
        }

        df = df.rename(columns=cols)


        summary_data = []
        for _, row in df.iterrows():
            summary_data.append(BillSummaryData(
                bill_id=self.instance,
                account_number=self.account_number,
                company=self.company_name,
                vendor=self.vendor_name,
                file_name=self.file_name,
                bill_date=self.bill_date,
                bill_day=self.bill_day,
                bill_month=self.bill_month,
                bill_year=self.bill_year,
                wireless_number=row.get("Wireless Number"),
                username=row.get("Username"),
                data_roaming=row.get("Data Roaming","NA"),
                message_roaming=row.get("Message Roaming","NA"),
                voice_roaming=row.get("Voice Roaming","NA"),
                data_usage=row.get("Data Usage","NA"),
                message_usage=row.get("Message Usage","NA"),
                voice_plan_usage=row.get("Voice Plan Usage","NA"),
                total_charges=row.get("Total Charges","NA"),
                third_party_charges=row.get("third_party_charges","NA"),
                taxes_governmental_surcharges=row.get("taxes_governmental_surcharges","NA"),
                other_charges_credits=row.get("other_charges_credits","NA"),
                usage_purchase_charges=row.get("usage_purchase_charges","NA"),
                equipment_charges=row.get("equipment_charges","NA"),
                plan=row.get("Plan"),
                monthly_charges=row.get("Monthly Charges"),
            ))
        BillSummaryData.objects.bulk_create(summary_data)

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

        df = df[list(cols.keys() & df.columns)].copy()
        for col in cols.keys():
            if col not in df.columns:
                df[col] = None

        df = df.rename(columns=cols)

        plan_charges_float = {
            p: self.safe_float(c)
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
                current_charge = self.safe_float(row.get("Charges"))
            except:
                return pd.Series([None, None, None])  # Invalid charges

            usage_val = row["Data Usage (GB)"]
            if pd.isna(usage_val) or usage_val == "NA":
                return pd.Series([None, None, None])

            try:
                usage = self.safe_float(row.get("Data Usage (GB)"))
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
        
        df[["Recommended Plan", "Recommended Plan Charges", "Recommended Plan Savings"]] = df.apply(suggest_plan, axis=1)
        df["is_plan_recommended"] = ~df["Recommended Plan"].isin(["", "NA", None])

        df['data_usage_value'] = (
            df['Data Usage (GB)']
            .astype(str)
            .str.extract(r'([\d.]+)')[0]
            .astype(float)
            .fillna(0)
        )

        mask_not_unlimited = ~df['Current Plan'].str.contains('unlimited', case=False, na=False)
        df.loc[df['data_usage_value'].isna() & mask_not_unlimited, 'data_usage_value'] = 0

        def classify_usage(row):
            plan = str(row['Current Plan']).lower()
            usage = row['data_usage_value']

            if pd.isna(usage):
                if 'unlimited' in plan:
                    return 'NA_unlimited'
                else:
                    return 'NA_not_unlimited'
            elif usage == 0:
                return 'zero_usage'
            elif usage < 5:
                return 'less_than_5_gb'
            elif 5 <= usage <= 15:
                return 'between_5_and_15_gb'
            else:
                return 'more_than_15_gb'
            

        df['data_usage_range'] = df.apply(classify_usage, axis=1)

        df.drop(columns=['data_usage_value'], inplace=True)
        df.loc[(df['data_usage_range'] == 'zero_usage') & (df['Data Usage (GB)'] == "NA"), 'Data Usage (GB)'] = 0

        df.to_csv("temp_df.csv")


        for col in ["Charges", "Recommended Plan Charges", "Recommended Plan Savings"]:
            df[col] = pd.to_numeric(
            df[col].astype(str).str.replace("$", "", regex=False), errors="coerce"
        )
            
        with transaction.atomic():

            for _, row in df.iterrows():
                obj, created = BillAnalysisData.objects.update_or_create(
                    account_number=self.account_number,
                    vendor=self.vendor_name,
                    wireless_number=row.get("Wireless Number"),
                    defaults={
                        "bill_id": self.instance,
                        "company": self.company_name,
                        "file_name": self.file_name,
                        "bill_date": self.bill_date,
                        "bill_day": self.bill_day,
                        "bill_month": self.bill_month,
                        "bill_year": self.bill_year,
                        "user_name": row.get("User Name"),
                        "current_plan": row.get("Current Plan"),
                        "current_plan_charges": row.get("Charges"),
                        "current_plan_usage": row.get("Data Usage (GB)"),
                        "data_usage_range": row.get("data_usage_range"),
                        "recommended_plan": row.get("Recommended Plan"),
                        "recommended_plan_charges": (
                            row.get("Recommended Plan Charges")
                            if pd.notna(row.get("Recommended Plan Charges")) else None
                        ),
                        "recommended_plan_savings": (
                            row.get("Recommended Plan Savings")
                            if pd.notna(row.get("Recommended Plan Savings")) else None
                        ),
                        "is_plan_recommended": row.get("is_plan_recommended", False),
                    }
                )
    
    def process(self):
        print("def process")
        try:
            start = time.perf_counter()
            print("Processing files...")

            if "verizon" in self.vendor_name.lower():
                Script = VerizonClass
            elif "mobile" in self.vendor_name.lower():
                if self.t_mobile_type == 1 :
                    Script = Tmobile1Class 
                elif self.t_mobile_type == 2:
                    Script =  Tmobile2Class
                else:
                    return False, "Invalid type for T-Mobile", 0, 1
            else:
                Script = AttClass

            

            if self.file_name.endswith(".pdf"):
                df = self.process_pdf_file_separately(path=self.filepath, Script=Script)
            elif self.file_name.endswith(".zip"):
                df = self.process_zip_file_separately(path=self.filepath)
            else:
                df = pd.DataFrame()
            
            df.to_csv("input_df.csv", index=False)  # Debugging line

            self.account_number = df["Account Number"].iloc[0]
            self.bill_date = df["Bill Date"].iloc[0]
            formatted_date = self.parse_bill_date(self.bill_date)
            self.bill_day = formatted_date.day
            self.bill_month = formatted_date.month
            self.bill_year = formatted_date.year

        
            self.manage_plans(df)
            self.insert_summary_and_analytics(df)
        
            end = time.perf_counter()
            return True, "Processing completed successfully", end - start, 0
        except Exception as e:
            print(f"Error during file processing: {e}")
            return False, f"Error during file processing: {e}", 0, 1

