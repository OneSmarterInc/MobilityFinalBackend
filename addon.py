
import json
import os
import zipfile
import pandas as pd
import shutil

def parse_until_dict(data):
    while isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            break
    return data

def str_to_bool(value):
    print(value)
    return str(value).strip().lower() in ['true','yes']

import re

def remove_digits_and_symbols(text):
    
    return re.sub(r'[^a-zA-Z\s]', '', text)
def string_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    min_len = min(len(a), len(b))
    matches = sum(1 for i in range(min_len) if a[i] == b[i])
    return matches / max(len(a), len(b))


def get_close_match_key(target_key: str, key_list: list[str]) -> str | None:
    closest = ""
    max_similarity = 0.0

    for candidate in key_list:
        target_key_enhanced = remove_digits_and_symbols(target_key)
        candidate_enhanced = remove_digits_and_symbols(candidate)
        sim = string_similarity(target_key_enhanced, candidate_enhanced)
        if sim > 0.8 and sim > max_similarity:
            max_similarity = sim
            closest = candidate

    return closest if closest else None

def compare(str1, str2):
    str1lst = str1.split()
    str2lst = str2.split()
    points = 0
    for i in str2lst:
       if i in str1lst: points+=1 
    percent = (points/len(str2lst)) * 100
    return int(percent) > 80
    


def extract_data_from_zip(path):
    extract_dir = 'Bills/media/extracted_files'
    os.makedirs(extract_dir, exist_ok=True)
    dataframes = []

    try:
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except zipfile.BadZipFile:   # correct exception name in py3
        return {'message': 'Invalid zip file', 'error': -1}
    except Exception as e:
        print("Error extracting zip data=", str(e))
        return {'message': str(e), 'error': -1}

    for root, _, files in os.walk(extract_dir):
        for file in files:
            file_path = os.path.join(root, file)

            try:
                if file.endswith((".xlsx", ".xls")):
                    df = pd.read_excel(file_path)
                    dataframes.append(df)

                elif file.endswith(".csv"):
                    df = pd.read_csv(file_path)
                    dataframes.append(df)

                elif file.endswith(".txt"):
                    df = pd.read_csv(file_path, delimiter="\t", engine="python")
                    dataframes.append(df)

            except Exception as e:
                print(f"Skipping {file}: {e}")
    
    shutil.rmtree(extract_dir)
    
    return [df for df in dataframes if not df.empty]

# frames = extract_data_from_zip('Bills/media/BanUploadBill/RDD_BUILD-A-BEAR_WORKSHOP_INC_202401.zip')
# for frame in frames:
#     print(frame)
# if not frames:
#     second_largest_df = None
# else:
#     unique_dfs = [df for df in frames if df["Wireless Number"].is_unique]

#     if unique_dfs:
#         second_largest_df = unique_dfs[0] 
#     else:
#         second_largest_df = frames[0]

# print(second_largest_df)
# # df = second_largest_df[["Wireless Number", "User Name", "Your Calling Plan", "Monthly Charges", "Data Usage (GB)"]]
# #remove rows where Wireless Number not match regex pattern of phone number 123-456-7890 or (123) 456-7890 or 123.456.7890
# df = df[df["Wireless Number"].str.match(r'^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', na=False)]
# # split Your Current Plan by first dollar amount and and get first part before renaming column to Plan
# df["Your Calling Plan"] = df["Your Calling Plan"].apply(lambda x: x.split('$')[0].strip() if '$' in x else x)
# df = df.rename(columns={"Your Calling Plan": "Plan", "Data Usage (GB)": "Data Usage", "User Name": "Username"}, errors='ignore')
# # add dollar sign to Monthly Charges if not present
# df["Monthly Charges"] = df["Monthly Charges"].apply(lambda x: f"${x}" if isinstance(x, (int, float)) else x)
# # add GB to data usage
# df["Data Usage"] = df["Data Usage"].astype(str).str.strip()

# df["Data Usage"] = df["Data Usage"].apply(
#     lambda x: x if x.endswith("GB") else f"{x} GB"
# )

# all_plans = df["Plan"].unique()
# plan_charges = (
#     df.dropna(subset=["Plan", "Monthly Charges"])
#         .groupby("Plan", as_index=False)["Monthly Charges"].min()
#         .set_index("Plan")["Monthly Charges"]
#         .to_dict()
# )

# print(all_plans)
# print(plan_charges)

# print(df.tail())

# def split_sheets(datadf):
#     # Make a copy to avoid warnings
#     datadf = datadf.copy()

#     # Define column mapping
#     cols = {
#         "Wireless Number": "Wireless Number",
#         "Username": "User Name",
#         "Plan": "Current Plan",
#         "Data Usage": "Data Usage (GB)",
#         "Monthly Charges": "Charges",
#         "Recommended Plan": "Recommended Plan",
#         "Recommended Plan Charges": "Recommended Plan Charges",
#         "Recommended Plan Savings": "Recommended Plan Savings",
#     }

#     # Select only available columns + add missing ones as empty
#     base_df = datadf[list(cols.keys() & datadf.columns)].copy()
#     for col in cols.keys():
#         if col not in base_df.columns:
#             base_df[col] = None

#     # Rename columns
#     base_df = base_df.rename(columns=cols)

#     # Reorder columns
#     column_order = [
#         "Wireless Number",
#         "User Name",
#         "Current Plan",
#         "Data Usage (GB)",
#         "Charges",
#         "Recommended Plan",
#         "Recommended Plan Charges",
#         "Recommended Plan Savings",
#     ]
#     base_df = base_df[column_order]

#     # --- Recommendation Logic ---
#     plan_charges_float = {p: float(c.replace("$", "")) for p, c in plan_charges.items()}

#     def extract_gb(plan_name: str):
#         """
#         Extract GB limit from plan name.
#         Returns float if found, otherwise None.
#         Handles cases like '10 GB', '5GB', '5GBHS'.
#         """
#         if not plan_name:
#             return None

#         match = re.search(r"(\d+(?:\.\d+)?)\s*GB", plan_name.upper())
#         if match:
#             try:
#                 return float(match.group(1))
#             except:
#                 return None
#         return None

#     def suggest_plan(row):
#         current_plan = row["Current Plan"]
#         try:
#             current_charge = float(row["Charges"].replace("$", ""))
#         except:
#             return pd.Series([None, None, None])  # Invalid charges

#         usage_val = row["Data Usage (GB)"]
#         if pd.isna(usage_val) or usage_val == "NA":
#             return pd.Series([None, None, None])

#         try:
#             usage = float(str(usage_val).replace("GB", ""))
#         except:
#             usage = 0.0

#         candidate_plans = []
#         for plan in all_plans:
#             gb_limit = extract_gb(plan)
#             if gb_limit is not None and usage <= gb_limit:
#                 candidate_plans.append((plan, plan_charges_float.get(plan, float("inf"))))
#         if candidate_plans:
#             # Pick cheapest valid plan
#             recommended_plan, rec_charge = min(candidate_plans, key=lambda x: x[1])
#             if recommended_plan != current_plan and rec_charge < current_charge:
#                 savings = float(current_charge - rec_charge)
#                 # savings with 2 decimal places after point
#                 savings_str = f"${savings:.2f}"
#                 rec_charge_str = f"${rec_charge:.2f}"
#                 return pd.Series([recommended_plan, rec_charge_str, savings_str])

#         return pd.Series([None, None, None])

    
#     print(base_df.tail())
#     base_df[["Recommended Plan", "Recommended Plan Charges", "Recommended Plan Savings"]] = base_df.apply(suggest_plan, axis=1)

#     na_df = base_df[base_df["Data Usage (GB)"] == "NA"].copy()
#     non_na_df = base_df[base_df["Data Usage (GB)"] != "NA"].copy()

#     # replace GB only if present


#     data_usage = (
#         non_na_df["Data Usage (GB)"].str.replace("GB", "", regex=False).astype(float)
#     )

#     sheet2 = non_na_df[data_usage <= 0].copy()
#     sheet3 = non_na_df[(data_usage > 0) & (data_usage <= 5)].copy()
#     sheet4 = non_na_df[(data_usage > 5) & (data_usage <= 15)].copy()
#     sheet5 = non_na_df[data_usage > 15].copy()

#     sheet6 = na_df[~na_df["Current Plan"].str.contains("Unlimited", case=False, na=False)].copy()
#     sheet7 = na_df[na_df["Current Plan"].str.contains("Unlimited", case=False, na=False)].copy()

#     return sheet2, sheet3, sheet4, sheet5, sheet6, sheet7

# def export_to_excel(line_items, filename="usage_report.xlsx"):
#         # Split into sheets
#         sheet2, sheet3, sheet4, sheet5,sheet6, sheet7  = split_sheets(line_items)
        
#         # Create Excel with 5 sheets
#         with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
#             # Sheet1 → all data
#             line_items.to_excel(writer, sheet_name="All Items", index=False)

#             # Other sheets
#             sheet2.to_excel(writer, sheet_name="Zero Usage Line", index=False)
#             sheet3.to_excel(writer, sheet_name="< 5GB", index=False)
#             sheet4.to_excel(writer, sheet_name="5 to 15GB", index=False)
#             sheet5.to_excel(writer, sheet_name="> 15GB", index=False)
#             sheet6.to_excel(writer, sheet_name="NA - Not Unlimited", index=False)
#             sheet7.to_excel(writer, sheet_name="NA - Unlimited", index=False)

# # export_to_excel(df)
