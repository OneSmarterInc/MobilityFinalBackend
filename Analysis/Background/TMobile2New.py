import pandas as pd
import pdfplumber,re,time

class Tmobile2Class:
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
        self.unique_key_pattern = re.compile(
            r'\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}.*?(?:p\.\d+)?(?:.*?(?:\$\d+(?:\.\d{2})?|-))+',
            re.IGNORECASE
        )
        self.details_key_pattern = re.compile(r"^[A-Z][a-z]+\s*,\s*\(?\d{3}\)?[.\s-]?\d{3}[.\s-]?\d{4}", re.IGNORECASE)
        self.key = None

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
        top_half_bbox = (0, 0, width, height / 2)
        bottom_half_bbox = (0, height / 2, width, height)
        top_half = page.within_bbox(top_half_bbox)
        bottom_half = page.within_bbox(bottom_half_bbox)
        top_text = top_half.extract_text()
        bottom_text = bottom_half.extract_text()

        topLines = top_text.splitlines()
        bottomLines = bottom_text.splitlines()
        self.total_amount = 0
        for i,line in enumerate(topLines):
            if (("account" and "invoice") in line.lower()):
                nxtLine = topLines[i+1]
                items = nxtLine.strip().split(" ")[:-3]
                self.invoice_number = items[-1]
                self.account_number = items[-2]
                self.bill_period = " ".join(items[:-2])
                self.bill_date = self.bill_period.split("-")[1].strip().replace(",","")
            if "welcome" in line.lower():
                line = line.split("Welcome")[1]
                nxtLine = topLines[i+1]
                if not "your" in nxtLine.lower():
                    self.billing["name"] = f'{line} {nxtLine}'.strip().replace(",","")
                else:
                    self.billing["name"] = f'{line}'.strip().replace(",","")

        for i,line in enumerate(bottomLines):
            if "total due" in line.lower():
                items = line.strip().split(" ")
                nxtLine = bottomLines[i+1]
                self.total_amount = items[-1]
                nxtitems = nxtLine.strip().split(" ")
                self.due_date = " ".join(nxtitems[-3:]).replace(",","")
                break
            
        com = {
            "Account Number": self.account_number,
            "Bill Period": self.bill_period,
            "Invoice Number": self.invoice_number,
            "Total Amount": self.total_amount,
            "Bill Date": self.bill_date,
            "Due Date": self.due_date,
            "Billing Info": self.billing,
            "Remittance Info": self.remmitance,
            "Duration": self.duration,
            "Vendor Url": self.url
        }
        return com
        
    def unique_data(self,pages):
        lines_data = []
        final_unique = []
        print("def unique_data")
        for page in pages:
            data = page.extract_text()
            lines = data.splitlines()
            lines_data += [line.strip() for line in lines if re.search(self.unique_key_pattern, line.strip())]
        for line in lines_data:
            items = line.split(" ")
            final_unique.append({
                "Wireless Number": " ".join(items[0:2]),
                "Username": " ".join(items[2:-8]),
                "Page": items[-8],
                "Monthly Charges": items[-7],
                "Usage Charges": items[-6],
                "Equipment": items[-5],
                "Services": items[-4],
                "One time Charges": items[-3],
                "Taxes and Fees": items[-2],
                "Total Charges": items[-1]
            })
        unique = pd.DataFrame(final_unique)
        unique = unique.replace(r'^\s*-\s*$', 'NA', regex=True)
        return unique
    def plan_data(self,pages,unique_df):
        print("def baseline data")
        wnplans = {}
        charges_data = []
        final_plan_data = []
        page = pages[0]
        width = page.width
        height = page.height

        self.wn = None
        leftBox = (0, 50, width/2, height-50)
        rightBox = (width/2, 50, width, height-50)
        wn_pattern = r'^\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\s+\$\d+(?:\.\d{2})?$'
        subcat_pattern = r'^[A-Za-z][A-Za-z0-9]*.*(?:\$\d+(?:\.\d{2})?|included)$'
        self.category = None
        self.plans = ""
        for page in pages:
            leftText = page.within_bbox(leftBox).extract_text()
            rightText = page.within_bbox(rightBox).extract_text()
            totalText = f'{leftText}\n{rightText}'
            totalText = re.sub(r'\b[A-Z][a-z]{2}\s+\d{1,2}\s*-\s*[A-Z][a-z]{2}\s+\d{1,2}\b', '', totalText)
    
            lines = totalText.splitlines()
            for line in lines:
                if re.search(wn_pattern, line.strip()):
                    items = line.split(" ")
                    self.wn = " ".join(items[:-1])
                    self.key = None
                    self.plans = ""
                if self.wn and line.strip().isupper():
                    
                    items = line.split(" ")
                    self.category = " ".join(items[:-1])
                    if "USAGE" in line.strip().upper():
                        self.category = None
                        self.key = "usage"
                        wnplans[self.wn] = ""      
                if self.key == "usage":
                    if "usage" not in line.lower():
                        items = line.strip().split(" ")
                        line = line.strip() 
                        newLine = " ".join(items[0:3]) if "Data" in items else " ".join(items[0:2])
                        wnplans[self.wn] += f"{newLine}" if "data" in newLine.lower() else ""
                if self.category and not line.strip().isupper() and re.search(subcat_pattern, line.strip()):
                    items = line.split(" ")
                    subcat = " ".join(items[:-1])
                    charges = items[-1]
                    charges_data.append({
                        "Wireless Number":self.wn,
                        "Item Category": self.category,
                        "Item Description": subcat,
                        "Charges": charges if '$' in charges else "$0.0"
                    })

        for wn, plans in wnplans.items():
            get_usage = plans.split(" ")[1]
            final_plan_data.append({
                "Wireless Number": wn,
                "Plan": plans.strip(),
                "Data Usage": get_usage if get_usage else "NA"
            })
        df = pd.DataFrame(charges_data)       
        if unique_df is not None:
            baseline_df = pd.merge(unique_df, df, on="Wireless Number")  
        else:
            baseline_df = df
        planDf = pd.DataFrame(final_plan_data)
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
                if (("account" and "invoice") in text.lower()):
                    if not matching_page_basic:
                        matching_page_basic.append(page)
                if text and "OVERVIEW" in text.upper():
                    matching_pages_unique.append(page)
                
                if text and "DETAILED CHARGES" in text.upper():
                    self.key = "detail"
                if text and ("WHAT YOU NEED TO KNOW" in text.upper() or "USAGE DETAILS" in text.upper()):
                    self.key = None
                    break
                if self.key:
                    # if matching_pages_baseline:
                    #     break
                    matching_pages_baseline.append(page)
        basic = self.initial_page_data(matching_page_basic)
        unique_df = self.unique_data(matching_pages_unique)
        charges_list = list(unique_df["Total Charges"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(float))
        sum_of_total_charges = sum(charges_list)
        basic["Total Charges"] = f'${round(sum_of_total_charges,2)}'
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
        return basic, self.format_wn(unique_df), round(float(tt), 2)
        
    

# path = "Bills/Scripts/t-mobiles/Type2/T_mobile.pdf"
# obj = Tmobile2Class(path)
# basic, plandf,t = obj.extract_all()
# print(basic)
# print(plandf)
# plandf.to_csv("plandf.csv", index=False)