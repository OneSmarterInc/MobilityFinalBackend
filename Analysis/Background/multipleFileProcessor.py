
import json

from AnalysisScripts.VerizonNew import VerizonClass
from AnalysisScripts.AttNew import AttClass
from AnalysisScripts.TMobile1New import Tmobile1Class
from AnalysisScripts.TMobile2New import Tmobile2Class

# from VerizonNew import VerizonClass
# from AttNew import AttClass
# from TMobile1New import Tmobile1Class
# from TMobile2New import Tmobile2Class
import pandas as pd
import re
import os,time
from django.core.files.base import File
from django.conf import settings
from ..models import AnalysisData
from ..models import SummaryData


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

    def process_file_separately(self,path, Script):
        try:
            scripter = Script(path)
            basic_data, line_items, processing_time = scripter.extract_all()
            self.account_number = basic_data.get("Account Number")
            line_items["Monthly Charges"] = line_items["Monthly Charges"].apply(lambda x: f"${x}" if isinstance(x, (int, float)) else x)
            line_items.insert(0, "Account Number", basic_data.get("Account Number"))
            line_items.insert(1, "Bill Date", basic_data.get("Bill Date"))
            return line_items
        except Exception as e:
            print(f"Error processing file: {e}")
            return pd.DataFrame()
        
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
        plan_charges_float = {p: float(c.replace("$", "")) for p, c in self.plan_charges.items()}

        def extract_gb(plan_name: str):
            """
            Extract GB limit from plan name.
            Returns float if found, otherwise None.
            Handles cases like '10 GB', '5GB', '5GBHS'.
            """
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
                current_charge = float(row["Charges"].replace("$", ""))
            except:
                return pd.Series([None, None, None])  # Invalid charges

            usage_val = row["Data Usage (GB)"]
            if pd.isna(usage_val) or usage_val == "NA":
                return pd.Series([None, None, None])

            try:
                usage = float(str(usage_val).replace("GB", ""))
            except:
                usage = 0.0

            candidate_plans = []
            for plan in self.all_plans:
                gb_limit = extract_gb(plan)
                if gb_limit is not None and usage <= gb_limit:
                    candidate_plans.append((plan, plan_charges_float.get(plan, float("inf"))))
            if candidate_plans:
                # Pick cheapest valid plan
                recommended_plan, rec_charge = min(candidate_plans, key=lambda x: x[1])
                if recommended_plan != current_plan and rec_charge < current_charge:
                    savings = float(current_charge - rec_charge)
                    # savings with 2 decimal places after point
                    savings_str = f"${savings:.2f}"
                    rec_charge_str = f"${rec_charge:.2f}"
                    return pd.Series([recommended_plan, rec_charge_str, savings_str])

            return pd.Series([None, None, None])

        

        base_df[["Recommended Plan", "Recommended Plan Charges", "Recommended Plan Savings"]] = base_df.apply(suggest_plan, axis=1)

        na_df = base_df[base_df["Data Usage (GB)"] == "NA"].copy()
        non_na_df = base_df[base_df["Data Usage (GB)"] != "NA"].copy()

        data_usage = (
            non_na_df["Data Usage (GB)"].str.replace("GB", "", regex=False).astype(float)
        )

        sheet2 = non_na_df[data_usage <= 0].copy()
        sheet3 = non_na_df[(data_usage > 0) & (data_usage <= 5)].copy()
        sheet4 = non_na_df[(data_usage > 5) & (data_usage <= 15)].copy()
        sheet5 = non_na_df[data_usage > 15].copy()

        sheet6 = na_df[~na_df["Current Plan"].str.contains("Unlimited", case=False, na=False)].copy()
        sheet7 = na_df[na_df["Current Plan"].str.contains("Unlimited", case=False, na=False)].copy()

        return sheet2, sheet3, sheet4, sheet5, sheet6, sheet7

    def export_to_excel(self, line_items, filename="usage_report.xlsx"):
        # Split into sheets
        sheet2, sheet3, sheet4, sheet5,sheet6, sheet7  = self.split_sheets(line_items)
        
        # Create Excel with 5 sheets
        with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
            # Sheet1 → all data
            line_items.to_excel(writer, sheet_name="All Items", index=False)

            # Other sheets
            sheet2.to_excel(writer, sheet_name="Zero Usage Line", index=False)
            sheet3.to_excel(writer, sheet_name="< 5GB", index=False)
            sheet4.to_excel(writer, sheet_name="5 to 15GB", index=False)
            sheet5.to_excel(writer, sheet_name="> 15GB", index=False)
            sheet6.to_excel(writer, sheet_name="NA - Not Unlimited", index=False)
            sheet7.to_excel(writer, sheet_name="NA - Unlimited", index=False)

        
        # Ensure BillAnalysis directory exists inside MEDIA_ROOT
        target_dir = os.path.join(settings.MEDIA_ROOT, "BillAnalysis")
        os.makedirs(target_dir, exist_ok=True)

        # Save only the basename so Django puts it in upload_to="BillAnalysis/"
        with open(filename, "rb") as f:
            django_file = File(f)
            self.instance.excel.save(os.path.basename(filename), django_file)

        self.instance.is_processed = True
        self.instance.save()

        # cleanup
        os.remove(filename)

        # Prepare data for AnalysisData model
        sheet2["data_type"] = "zero_usage"
        sheet3["data_type"] = "less_than_5_gb"
        sheet4["data_type"] = "between_5_and_15_gb"
        sheet5["data_type"] = "more_than_15_gb"
        sheet6["data_type"] = "NA_not_unlimited"
        sheet7["data_type"] = "NA_unlimited"

        all_data = pd.concat([sheet2, sheet3, sheet4, sheet5,sheet6, sheet7], ignore_index=True)
        all_data = all_data.merge(
            line_items[["Wireless Number", "Account Number", "Bill Date"]],
            on="Wireless Number",
            how="left"  
        )
        # rename columns to match AnalysisData model
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

        return all_data
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

    def add_data_to_db(self, data_df):
        print("saving to db")
        # convert charges and savings to numeric, errors='coerce' will set invalid parsing as NaN
        data_df["current_plan_charges"] = pd.to_numeric(
            data_df["current_plan_charges"].str.replace("$", "", regex=False), errors="coerce"
        )
        data_df["recommended_plan_charges"] = pd.to_numeric(
            data_df["recommended_plan_charges"].str.replace("$", "", regex=False), errors="coerce"
        )
        data_df["recommended_plan_savings"] = pd.to_numeric(
            data_df["recommended_plan_savings"].str.replace("$", "", regex=False), errors="coerce"
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
                data_type=row["data_type"],
                user_name=row["user_name"],
                current_plan=row["current_plan"],
                current_plan_charges=row["current_plan_charges"] if pd.notna(row["current_plan_charges"]) else None,
                current_plan_usage=row["current_plan_usage"],
                recommended_plan=row["recommended_plan"],
                recommended_plan_charges=row["recommended_plan_charges"] if pd.notna(row["recommended_plan_charges"]) else None,
                recommended_plan_savings=row["recommended_plan_savings"] if pd.notna(row["recommended_plan_savings"]) else None,
            )

    def add_gb(self, val):
        if pd.isna(val):   # leave NaN as is
            return val
        val_str = str(val).strip()
        if val_str.lower().endswith("gb"):
            return val_str
        return f"{val_str} GB"

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
            "Equipment Charges": "equipment_charges",
            "Usage and Purchase Charges": "usage_purchase_charges",
            "Plan": "plan",
            "Monthly Charges": "monthly_charges",
        })
        df["data_usage"] = df["data_usage"].apply(self.add_gb)
        df["monthly_charges"] = df["monthly_charges"].astype(str).str.replace("$", "", regex=False)
        df["usage_purchase_charges"] = df["usage_purchase_charges"].astype(str).str.replace("$", "", regex=False)
        df["equipment_charges"] = df["equipment_charges"].astype(str).str.replace("$", "", regex=False)
        df["other_charges_credits"] = df["other_charges_credits"].astype(str).str.replace("$", "", regex=False)
        df["taxes_governmental_surcharges"] = df["taxes_governmental_surcharges"].astype(str).str.replace("$", "", regex=False)
        df["third_party_charges"] = df["third_party_charges"].astype(str).str.replace("$", "", regex=False)
        df["total_charges"] = df["total_charges"].astype(str).str.replace("$", "", regex=False)
        
        model_fields = {f.name for f in SummaryData._meta.get_fields()}
        records = []
        for row in df.to_dict(orient="records"):
            filtered = {k: v for k, v in row.items() if k in model_fields}
            records.append(SummaryData(multiple_analysis=self.instance,**filtered))

        # bulk insert
        SummaryData.objects.bulk_create(records, ignore_conflicts=True)

        



    def process(self):
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
                df = self.process_file_separately(path=path, Script=Script)
                if not df.empty:
                    dfs.append(df)
            

            if not dfs:
                return False, "No valid files processed", 0, 1
            
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

            # Build output filename based on available Bill Dates
            dates = "_".join([str(df["Bill Date"].iloc[0]) for df in dfs if "Bill Date" in df.columns])
            output_file = f'{self.account_number}_{dates}.xlsx'.replace(" ", "_")

            # Export + DB save
            final_data = self.export_to_excel(df, filename=output_file)
            self.add_data_to_db(final_data)

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