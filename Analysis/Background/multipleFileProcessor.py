
import json

from AnalysisScripts.VerizonNew import VerizonClass
from AnalysisScripts.AttNew import AttClass
from AnalysisScripts.TMobile1New import Tmobile1Class
from AnalysisScripts.TMobile2New import Tmobile2Class
from django.core.files.base import ContentFile

# from VerizonNew import VerizonClass
# from AttNew import AttClass
# from TMobile1New import Tmobile1Class
# from TMobile2New import Tmobile2Class
import pandas as pd
import re, calendar
import os,time
from django.core.files.base import File
from django.conf import settings
from ..models import AnalysisData
from ..models import SummaryData
from dateutil import parser
import numpy as np
from addon import extract_data_from_zip
from .savingspdf import create_savings_pdf
from datetime import datetime

class MultipleFileProcessor:
    def __init__(self, instance, buffer_data):
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
        self.df1 = None
        self.df2 = None
        self.df3 = None

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
            bill_date = second_largest_df["Bill Date"].iloc[0]
            formatted_bill_date = self.parse_bill_date(bill_date)
            print("bill date", formatted_bill_date)
            second_largest_df["bill_day"] = formatted_bill_date.day
            second_largest_df["bill_month"] = formatted_bill_date.month
            second_largest_df["bill_year"] = formatted_bill_date.year
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
            formatted_bill_date = self.parse_bill_date(bill_date)
            line_items["bill_day"] = formatted_bill_date.day
            line_items["bill_month"] = formatted_bill_date.month
            line_items["bill_year"] = formatted_bill_date.year
            line_items["file_name"] = self.get_filename(path=path)
            return line_items
        except Exception as e:
            print(f"Error processing file: {e}")
            return pd.DataFrame()
        
    def parse_bill_date(self, date_str):
        try:
            return parser.parse(date_str, dayfirst=False)  # US-style month/day
        except Exception:
            raise ValueError(f"Date format not supported: {date_str}")

        
    def extract_highest_usage(self, *dfs):
        print("def extract_highest_usage")
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
            .astype(str)
            .str.replace("GB", "", regex=False)
            .str.strip()
        )
        combined["_usage_numeric"] = pd.to_numeric(
            combined["_usage_numeric"], errors="coerce"
        ).fillna(0)

        # Find row with max usage per Wireless Number
        idx = combined.groupby("Wireless Number")["_usage_numeric"].idxmax()

        # Select rows and drop helper column
        highest = combined.loc[idx].drop(columns="_usage_numeric").reset_index(drop=True)

        return highest
    
    def check_availability(self, all_dfs):
        print("def check_availability")
        combined = []

        print(all_dfs)

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


    
    def split_sheets(self, datadf):
        print("def split_sheets")
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
        frames = [df for df in [non_na_df, na_non_unlimited] if not df.empty and not df.isna().all().all()]
        non_na_df = pd.concat(frames, ignore_index=True)


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

        return sheet2, sheet3, sheet4, sheet5, sheet6

    def add_no_recommendation(self,dfs):
        print("Def add_no_recommendation")

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
        print("def check_usage_trend")
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


        return usage_wide

    def more_than_10_percent_var(self, v):
        try:
            return float(v.strip("%")) > 10
        except:
            return False
    def export_to_excel(self, original_dfs, line_items, filename="usage_report.xlsx"):
        print("def export_to_excel")
        sheet2, sheet3, sheet4, sheet5, sheet6 = self.split_sheets(line_items)
        sheet8 = self.check_usage_trend(original_dfs)
        STARTROW = 2
        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            excel_sheet2, excel_sheet3, excel_sheet4, excel_sheet5, excel_sheet6 = self.add_no_recommendation([sheet2, sheet3, sheet4, sheet5, sheet6])
            sheet7 = self.check_availability(original_dfs)
            get_top_10 = sheet8[sheet8["Variance"].apply(self.more_than_10_percent_var)]
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
            get_top_10.to_excel(writer, sheet_name="Data Usage Trend", index=False, startrow=STARTROW)

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
                    col_series = df_for_columns[col_name].fillna("").infer_objects(copy=False).astype(str)
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
            apply_sheet_format("Data Usage Trend", get_top_10)


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
        sheet2["data_usage_range"] = "zero_usage"
        sheet3["data_usage_range"] = "less_than_5_gb"
        sheet4["data_usage_range"] = "between_5_and_15_gb"
        sheet5["data_usage_range"] = "more_than_15_gb"
        sheet6["data_usage_range"] = "NA_unlimited"

        sheet8[["Variance", "Relation"]] = sheet8[["Variance", "Relation"]].replace("-", "NA")
        all_data = pd.concat([sheet2, sheet3, sheet4, sheet5, sheet6], ignore_index=True)

        all_data = (
            all_data.merge(
                line_items[["Wireless Number", "Account Number", "Bill Date"]],
                on="Wireless Number",
                how="left"
            )
            .merge(
                sheet8[["Wireless Number", "Variance", "Relation"]],
                on="Wireless Number",
                how="left"
            )
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

    def add_data_to_db(self, data_df):
        print("saving to db")
        # convert charges and savings to numeric, errors='coerce' will set invalid parsing as NaN
        for col in ["current_plan_charges", "recommended_plan_charges", "recommended_plan_savings"]:
            data_df[col] = pd.to_numeric(
                data_df[col].astype(str).str.replace("$", "", regex=False), errors="coerce"
            )

        data_df["current_plan_usage"] = data_df["current_plan_usage"].apply(self.add_gb)
        # data_df["current_plan_charges"] = data_df["current_plan_charges"].astype(str).str.replace("$", "", regex=False)
        # data_df["recommended_plan_charges"] = data_df["recommended_plan_charges"].astype(str).str.replace("$", "", regex=False)

        # just create new entries, even if wireless_number already exists
        for _, row in data_df.iterrows():
            obj = AnalysisData.objects.create(
                account_number=row["account_number"],
                bill_date=row["bill_date"],
                wireless_number=row["wireless_number"],
                multiple_analysis_id=row["multiple_analysis_id"],
                data_usage_range=row["data_usage_range"],
                user_name=row["user_name"],
                is_plan_recommended=row["is_plan_recommended"],
                current_plan=row["current_plan"],
                current_plan_charges=row["current_plan_charges"] if pd.notna(row["current_plan_charges"]) else None,
                current_plan_usage=row["current_plan_usage"],
                recommended_plan=row["recommended_plan"],
                variance_with_last_month=row["Variance"],
                how_variance_is_related_with_last_month=row["Relation"],
                file_name=row["file_name"],
                recommended_plan_charges=row["recommended_plan_charges"] if pd.notna(row["recommended_plan_charges"]) else None,
                recommended_plan_savings=row["recommended_plan_savings"] if pd.notna(row["recommended_plan_savings"]) else None,
            )
        savings=AnalysisData.objects.filter(multiple_analysis=self.instance).exclude(recommended_plan="").values("user_name", "wireless_number", "current_plan", "current_plan_charges", "current_plan_usage", "recommended_plan", "recommended_plan_charges", "recommended_plan_savings")
        df = pd.DataFrame(list(savings))
        return df
            

        

    def add_gb(self, val):
        if pd.isna(val):   # leave NaN as is
            return val
        val_str = str(val).strip()
        if val_str.lower().endswith("gb"):
            return val_str
        return f"{val_str} GB"

    def store_summary_data(self,df):
        print("def store summary data")
            
        
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
        print("def process")
        try:
            start = time.perf_counter()
            print("Processing files...")

            # Pick script based on vendor/type
            if "verizon" in self.vendor.lower():
                Script = VerizonClass
            elif "mobile" in self.vendor.lower():
                if self.type == 1 :
                    Script = Tmobile1Class 
                elif self.type == 2:
                    Script =  Tmobile2Class
                else:
                    return False, "Invalid type for T-Mobile", 0, 1
            else:
                Script = AttClass

            # Process each available file
            dfs = []
            for path in self.file_paths:
                if path.endswith(".pdf"):
                    df = self.process_pdf_file_separately(path=path, Script=Script)
                elif path.endswith(".zip"):
                    df = self.process_zip_file_separately(path=path)
                else:
                    df = pd.DataFrame()
                if not df.empty:
                    dfs.append(df)
        
            if not dfs:
                return False, "No valid files processed", 0, 1
            original_dfs = dfs
            for df in dfs:
                self.store_summary_data(df)
            

            # Check account numbers are consistent
            accounts = [df["Account Number"].iloc[0] for df in dfs if "Account Number" in df.columns]
            if len(set(accounts)) > 1:
                return False, f"Account Number mismatch detected! Found values: {accounts}", 0, 1

            self.account_number = accounts[0]

            # Manage plans
            for df in dfs:
                self.manage_plans(df)


            # Extract highest usage
            df = self.extract_highest_usage(*dfs, *(None,) * (3 - len(dfs)))


            dates = "_".join([str(df["Bill Date"].iloc[0]) for df in dfs if "Bill Date" in df.columns])
            output_file = f'{self.account_number}_{dates}.xlsx'.replace(" ", "_")

            final_data = self.export_to_excel(original_dfs, df, filename=output_file)

            final_data['bill_date_parsed'] = final_data['bill_date'].apply(self.parse_bill_date)

            final_data['bill_month'] = final_data['bill_date_parsed'].dt.month
            final_data['bill_year']  = final_data['bill_date_parsed'].dt.year

            unique_dates = final_data[['bill_month', 'bill_year']].drop_duplicates().sort_values(['bill_year', 'bill_month'])

            # Format into readable strings
            formatted_dates = [
                f"{calendar.month_name[row.bill_month]} {row.bill_year}"
                for row in unique_dates.itertuples(index=False)
            ]
            
            merged_df = final_data.merge(
                df[['Bill Date', 'Wireless Number', 'file_name']],
                left_on=['bill_date', 'wireless_number'],
                right_on=['Bill Date', 'Wireless Number'],
                how='left'
            )

            merged_df = merged_df.drop(columns=['Bill Date', 'Wireless Number'])
            savings_df=self.add_data_to_db(merged_df)

            # generate savings pdf

            pdf = create_savings_pdf(savings_df, self.account_number, formatted_dates)
            filename = f"savings_report_{self.account_number}_{formatted_dates}.pdf"
            pdf_file = ContentFile(pdf)
            self.instance.savings_pdf.save(filename, pdf_file)
            self.instance.save()
            end = time.perf_counter()
            return True, "Files processed successfully", round(end - start, 2), 1

        except Exception as e:
            print(f"Error in processing: {e}")
            return False, str(e), 0, 0
    
# buffer_data = {
#     'vendor': "Verizon",
#     'file1_path': 'Bills/Analysis/Background/VerizonTestBills/VerizonApr24.pdf',
#     'file2_path': 'Bills/Analysis/Background/VerizonTestBills/VerizonMay24.pdf',
#     # 'file3_path': 'Bills/Analysis/Background/VerizonTestBills/VerizonJun24.pdf',
# }

# obj = MultipleFileProcessor(buffer_data=buffer_data, instance=None)
# obj.process()