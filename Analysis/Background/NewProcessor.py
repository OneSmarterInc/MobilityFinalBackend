import json
from AnalysisScripts.VerizonNew import VerizonClass
from AnalysisScripts.AttNew import AttClass
from AnalysisScripts.TMobile1New import Tmobile1Class
from AnalysisScripts.TMobile2New import Tmobile2Class
import pandas as pd
import re
import os
from django.core.files.base import File
from django.conf import settings
from ..models import AnalysisData


class AnalysisProcessor:
    def __init__(self, instance, buffer_data):
        self.instance = instance
        self.buffer_data = json.loads(buffer_data) if isinstance(buffer_data,str) else buffer_data
        self.path = self.buffer_data.get('pdf_path')
        self.filename = self.buffer_data.get('pdf_filename').split("/")[-1]
        self.vendor = self.buffer_data.get('vendor_name')
        self.type = self.buffer_data.get('type')
        print("type==",self.type)
        self.all_plans = None
        self.plan_charges = None

    
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
        all_data["analysis_id"] = self.instance.id

        return all_data
        
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

        # just create new entries, even if wireless_number already exists
        for _, row in data_df.iterrows():
            obj = AnalysisData.objects.create(
                account_number=row["account_number"],
                bill_date=row["bill_date"],
                wireless_number=row["wireless_number"],
                analysis_id=row["analysis_id"],
                data_type=row["data_type"],
                user_name=row["user_name"],
                current_plan=row["current_plan"],
                current_plan_charges=row["current_plan_charges"] if pd.notna(row["current_plan_charges"]) else None,
                current_plan_usage=row["current_plan_usage"],
                recommended_plan=row["recommended_plan"],
                recommended_plan_charges=row["recommended_plan_charges"] if pd.notna(row["recommended_plan_charges"]) else None,
                recommended_plan_savings=row["recommended_plan_savings"] if pd.notna(row["recommended_plan_savings"]) else None,
            )

        

        
    def process(self):
        try:
            print("def process_analysis_pdf_from_buffer")
            if "verizon" in self.vendor.lower():
                scripter = VerizonClass(self.path)
            elif "mobile" in self.vendor.lower():
                if self.type == 1:
                    scripter = Tmobile1Class(self.path)
                elif self.type == 2:
                    scripter = Tmobile2Class(self.path)
                else:
                    return False, 'Invalid type for T-Mobile', 0
            else:
                scripter = AttClass(self.path)
            basic_data, line_items, processing_time = scripter.extract_all()
            line_items["Monthly Charges"] = line_items["Monthly Charges"].apply(lambda x: f"${x}" if isinstance(x, (int, float)) else x)
            line_items.insert(0, "Account Number", basic_data.get("Account Number"))
            line_items.insert(1, "Bill Date", basic_data.get("Bill Date"))

            self.all_plans = line_items["Plan"].unique()
            self.plan_charges = (
                line_items.dropna(subset=["Plan", "Monthly Charges"])
                    .groupby("Plan", as_index=False)["Monthly Charges"].min()
                    .set_index("Plan")["Monthly Charges"]
                    .to_dict()
            )
            
            print("Script processing time:", processing_time, "seconds")
            final_data = self.export_to_excel(line_items, filename=self.filename.replace(".pdf", ".xlsx"))
            # Save to AnalysisData model
            self.add_data_to_db(final_data)
            
            return True, 'PDF processed successfully', processing_time
        except Exception as e:
            print(e)
            if self.instance and self.instance.pk: self.instance.delete()
            return False, str(e), 0



# path = "Bills/Scripts/t-mobiles/Type2/T_mobile.pdf"

# buffer_data = json.dumps(
#     {'pdf_path':path, 'vendor_name':"T-Mobile", "type":2, 'pdf_filename':path.split("/")[-1], 'user_id':21, 'organization':"babw", 'remark':"remark"}
# )
# obj = AnalysisProcessor(instance=None, buffer_data=buffer_data)
# obj.process()