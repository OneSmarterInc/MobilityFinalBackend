import pandas as pd
import pdfplumber,re,time

import pandas as pd
import pdfplumber,re

class AttClass:
    def __init__(self,path):
        self.path = path
        self.account_number = None
        self.invoice_number = None
        self.bill_date = None
        self.bill_period = None
        self.key = None
        self.unique_key_pattern = re.compile(r'(?:\d{3}[-.]){2}\d{4}\s+[A-Za-z]+\s+[A-Za-z]+\s+\d+\s+(?:\$\d+(?:\.\d{2})?|-)', re.IGNORECASE)
        self.details_key_pattern = re.compile(r"(?=.*\bTotal\b)(?=.*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", re.IGNORECASE)

    def initial_page_data(self,pages):
        print("def initial_page_data")
        print(pages)
        page = pages[0]

        width = page.width
        height = page.height
        top_half_bbox = (0, 0, width, height / 2)
        bottom_half_bbox = (0, height / 2, width, height)
        top_half = page.within_bbox(top_half_bbox)
        bottom_half = page.within_bbox(bottom_half_bbox)
        top_text = top_half.extract_text()
        bottom_text = bottom_half.extract_text()

        account_number_match = re.search(r"Account Number: ([\d\-]+)", top_text)
        self.account_number = account_number_match.group(1) if account_number_match else None
        print("Account Number:", self.account_number)
        invoice_number_match = re.search(r"Invoice: (\d+)", top_text)
        self.invoice_number = invoice_number_match.group(1) if invoice_number_match else None
        print("Invoice Number:", self.invoice_number)
    def unique_data(self,pages):
        pass
    def baseline_data(self,pages):
        pass

    def extract_all(self):
        matching_page_basic = []
        matching_pages_unique = []
        matching_pages_baseline = []
        with pdfplumber.open(self.path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not self.key and (("account" and "invoice") in text.lower()):
                    if not matching_page_basic:
                        matching_page_basic.append(page)
                if text and self.unique_key_pattern.search(text):
                    matching_pages_unique.append(page)
                if text and self.details_key_pattern.search(text):
                    matching_pages_baseline.append(page)
            # print(matching_page_basic)
            # print(len(matching_pages_unique),matching_pages_unique)
            # print(len(matching_pages_baseline))
            self.initial_page_data(matching_page_basic)
            self.unique_data(matching_pages_unique)
            self.baseline_data(matching_pages_baseline)
            
                    
        # print(matching_pages[10])
        
    




obj = AttClass("Bills/media/BanUploadBill/ATT_Mobility_MPP.pdf")
obj.extract_all()
# print(unique[["Wireless Number", "Plans"]].head(10))
# unique.to_csv("unique.csv", index=False)
# baseline.to_csv("baseline.csv", index=False)