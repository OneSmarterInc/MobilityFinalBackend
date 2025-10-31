import pandas as pd
import pdfplumber,re,time

class Tmobile1Class:
    def __init__(self,path):
        self.path = path
        self.account_number = None
        self.invoice_number = None
        self.bill_date = None
        self.due_date = None
        self.bill_period = None
        self.key = None
        self.url = "https://www.t-mobile.com/"
        self.billing = {}
        self.remmitance = "P.O. Box 742596 Cincinnati, OH 45274-2596"
        self.duration = None
        self.details_key_pattern = re.compile(r"^[A-Z][a-z]+\s*,\s*\(?\d{3}\)?[.\s-]?\d{3}[.\s-]?\d{4}", re.IGNORECASE)
        self.planSide = None

    def format_wn(self, df):
        if not "Wireless Number" in df.columns:
            return df
        df["Wireless Number"] = (
            df["Wireless Number"]
            .astype(str)
            .str.replace(r"\D", "", regex=True)
            .str.replace(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", regex=True)
        )
        return df
    
    def initial_page_data(self,pages):
    
        print("def initial_page_data")
        page = pages[0]
        width = page.width
        
        height = page.height
        top_half_bbox = (width/2, 100, width, height / 2)
        bottom_left_half_bbox = (0, height / 2 + 150, width/2, height-100)
        bottom_right_half_bbox = (width/2, height / 2 + 150, width, height-100)
        top_half = page.within_bbox(top_half_bbox)
        bottom_left_half = page.within_bbox(bottom_left_half_bbox)
        bottom_right_half = page.within_bbox(bottom_right_half_bbox)
        top_text = top_half.extract_text()
        bottom_left_text = bottom_left_half.extract_text()
        bottom_right_text = bottom_right_half.extract_text()

        topLines = top_text.splitlines()
        bottomleftLines = bottom_left_text.splitlines()
        bottomrightLines = bottom_right_text.splitlines()
        self.total_amount = 0
        self.billing["name"] = topLines[0]
        self.billing["address"] = " ".join(topLines[1:])

        self.remmitance = " ".join(bottomleftLines[1:])
        
        for i,line in enumerate(bottomrightLines):
            
            if "account" in line.lower():
                line = line.replace(" ","")
                self.account_number = line.split(":")[1]
            if "$" in line.lower():
                line = line.replace(" ","")
                self.total_amount = line
            if "due" in line.lower():
                self.due_date = bottomrightLines[i+1].split(" ")[1]

        com = {
            "Account Number": self.account_number,
            "Bill Period": self.bill_period,
            "Invoice Number": self.invoice_number,
            "Total Amount": self.total_amount,
            "Due Date": self.due_date,
            "Billing Info": self.billing,
            "Remittance Info": self.remmitance,
            "Duration": self.duration,
            "Vendor Url": self.url
        }
        return com
        
    def unique_data(self,pages):
        unique_data = []
        print("def unique_data")
        page = pages[0]
        self.wn = None
        text = page.within_bbox((0, 0, page.width/2, 200)).extract_text()
        # to get date of an
        pattern = re.compile(r"""
            (                       
            (?:[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}) 
            )                       
        """, re.VERBOSE)
        matches = pattern.search(text)
        self.bill_date = matches[0].replace(",","") if matches else None
        print("bill date===",self.bill_date)
        for page in pages:
            text = page.extract_text()
            lines = text.splitlines()
            lines = [f'{line.replace("$","")} {lines[i+1].replace("(","").replace(")","").split(" ")[-1]}'  for i,line in enumerate(lines[:-1]) if "details on page" in lines[i+1].lower()]
            for line in lines:
                items = [item for item in line.split(" ") if item]
                unique_data.append({
                    "Wireless Number" : "".join(items[0:-9]),
                    "Page": items[-1],
                    "Username": "",
                    "Monthly Charges": f'${items[-9]}',
                    "Credits & Adjustments": f'${items[-8]}',
                    "Usage Charges": f'${items[-7]}',
                    "One Time Charges": f'${items[-6]}',
                    "Other Charges": f'${items[-5]}',
                    "Third Party Services": f'${items[-4]}',
                    "Taxes and Surcharges": f'${items[-3]}',
                    "Total Charges": f'$ {items[-2]}', 
                })

            

        df = pd.DataFrame(unique_data).replace(r'^\s*\$?-\s*$', 'NA', regex=True)
        return df
    def separate_words(self, text):
        words = re.findall(r'[A-Z][a-z]*|[a-z]+|[A-Z]+(?![a-z])', text)
        for word in words:
            if "Charges" in word and len(word) > len("Charges"):
                separate = list(str(word).strip().partition("Charges"))
                newWord = " ".join(separate).strip()
                words[words.index(word)] = newWord
        return " ".join(words)
    def plan_data(self,pages,unique_df):
        print("def baseline data")
        all_charges_text = {}
        all_plans_text = {}
        final_charges_data = []
        final_plan_data = []
        self.wn = None
        self.key = None
        
        for page in pages:
            lines = page.extract_text().splitlines()
            for line in lines:
                if "subscriber service detail" in line.lower():
                    items = line.split(" ")
                    self.wn = " ".join(items[-2:])
                    all_charges_text[self.wn] = ""
                    all_plans_text[self.wn] = ""
                if self.wn:
                    if "used service" in line.lower():
                        self.key = "service"
                        all_plans_text[self.wn] = ""
                    # if "used service" in line.lower():
                    #     self.key = None
                    if (("total" and "amount")) in line.lower():
                        self.key = "charges"
                    if self.key == "charges":
                        all_charges_text[self.wn] += f'{line}\n' 
                    if self.key == "service" and not self.key in line.lower():
                        all_plans_text[self.wn] += f'{line}\n' 
                if "total charges" in line.lower():
                    self.wn = None
                    self.key = None
        self.cat = None
        for wn, chargesText in all_charges_text.items():
            lines = [line.replace("&","And").replace("and","And") for line in chargesText.splitlines() if "$" in line]
            for line in lines:
                cat = "".join(line.split(" ")).split("$")[0]
                separated = self.separate_words(cat).replace("T Mobile","T-Mobile")
                if cat.lower().endswith(("es","charges")):
                    self.cat = separated
                if self.cat and self.cat.split(" ")[-1] not in separated:
                    splitted = line.split("$")
                    desc = " ".join(splitted[:-1])
                    chrgs = f'${splitted[-1].strip()}'
                    final_charges_data.append({
                        "Wireless Number": wn,
                        "Item Category": self.cat,
                        "Item Description": desc,
                        "Charges": chrgs if "." in chrgs else "$0.0"
                    })
                if "total" in line.lower():
                    self.cat = None
        
        for wn, plansText in all_plans_text.items():
            self.usage = ""
            keys = ("gigabytes", "messages", "minutes")
            lines = [line for line in plansText.splitlines() if "gigabytes" in line.lower() and not ("total" in line.lower() or "subscriber service detail" in line.lower())]
            for line in lines: 
                peak = line.split(" ")[-3]
                
                self.usage += f"{peak}"
            final_plan_data.append({
                "Wireless Number": wn,
                "Plan": "",
                "Data Usage": self.usage.strip() if self.usage else "NA"
            })
                

        df = self.format_wn(pd.DataFrame(final_charges_data))
        if unique_df is not None:
            baseline_df = pd.merge(unique_df, df, on="Wireless Number")  
        else:
            baseline_df = df
        planDf = self.format_wn(pd.DataFrame(final_plan_data))
        if not planDf.empty:
            planDf["Plan"] = planDf["Plan"].apply(lambda x: x.strip())
            planDf["Plan"] = planDf["Plan"].apply(lambda x: x.replace("  ", " "))
            baseline_df = pd.merge(baseline_df, planDf, on="Wireless Number") 

        if "Item Description" in baseline_df.columns and "Plan" in baseline_df.columns:
            desc_map = baseline_df.groupby("Wireless Number")["Item Description"].first().to_dict()
            baseline_df["Plan"] = baseline_df["Wireless Number"].map(desc_map).fillna(baseline_df["Plan"])
            baseline_df = baseline_df.drop(columns=["Item Description"])
        
        return baseline_df
    def extract_all(self):
        start_time = time.perf_counter()
        matching_page_basic = []
        matching_pages_unique = []
        matching_pages_baseline = []
        with pdfplumber.open(self.path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if (("account") in text.lower()):
                    if not matching_page_basic:
                        matching_page_basic.append(page)
                if "monthly summary" in text.lower():
                    matching_pages_unique.append(page)
                if "subscriber service detail" in text.lower():
                    # if matching_pages_baseline:
                    #     break
                    matching_pages_baseline.append(page)
        basic = self.initial_page_data(matching_page_basic)
        
        unique_df = self.unique_data(matching_pages_unique)
        
        # unique df charges
        # charges_list = list(unique_df["Total Charges"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(float))
        # sum_of_total_charges = sum(charges_list)
        # print("unique df sum=",round(sum_of_total_charges,2))
        baseline_df = self.plan_data(matching_pages_baseline,unique_df)
        
        plan_df = baseline_df[["Wireless Number", "Plan", "Data Usage"]]
        plan_df = plan_df.drop_duplicates(subset=["Wireless Number", "Plan"])
        unique_df = unique_df.merge(plan_df, on="Wireless Number", how="left")
        
        # reorder unique df to put Plan just before Monthly Charges
        if "Plan" in unique_df.columns:
            cols = list(unique_df.columns)
            plan_index = cols.index("Plan")
            monthly_index = cols.index("Monthly Charges")
            if plan_index > monthly_index:
                cols.insert(monthly_index, cols.pop(plan_index))
            unique_df = unique_df[cols]
        else:
            unique_df.insert(unique_df.columns.get_loc("Monthly Charges"), "Plan", "")
        


        process_finish_time = time.perf_counter()
        tt = process_finish_time - start_time
        basic["Bill Date"] = self.bill_date
        return basic, self.format_wn(unique_df), round(float(tt), 2)
        
    

# path = "/home/marshal19/Desktop/BillsProject/Bills/media/ViewUploadedBills/aug-Tmob.pdf"
# obj = Tmobile1Class(path)
# basic, plandf,t = obj.extract_all()
# print(basic)
# print(plandf)
# plandf.to_csv("plandf.csv", index=False)