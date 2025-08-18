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
        self.unique_key_pattern = re.compile(r'(?:\d{3}[-.]){2}\d{4}\s+[A-Za-z]+\s+[A-Za-z]+\s+\d+\s+(?:\$\d+(?:\.\d{2})?|-)', re.IGNORECASE)
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
        self.x0 = width/2
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
        print("def unique_data")
    def baseline_data(self,pages,unique_df):
        print("def baseline data")
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

                        break
        basic = self.initial_page_data(matching_page_basic)
        unique_df = self.unique_data(matching_pages_unique)
        baseline_df = self.baseline_data(matching_pages_baseline,unique_df)

        process_finish_time = time.perf_counter()
        tt = process_finish_time - start_time
        # return basic, self.format_wn(unique_df), self.format_wn(baseline_df), round(float(tt), 2)
        return basic, unique_df,baseline_df, round(float(tt), 2)
        
    

# path = "Bills/Scripts/t-mobiles/T-Mobile Bill.pdf"
# obj = Tmobile1Class(path)
# basic, unique_df, baseline_df,totalTime = obj.extract_all()
# print(basic)
# print(totalTime)

    