import pandas as pd
import pdfplumber
import re

class Verizon2:
    def __init__(self,path):
        self.path = path
        self.account_number = None
        self.invoice_number = None
        self.bill_date = None
        self.bill_period = None
        self.details_key_pattern = re.compile(r'Total\s+Current\s+Charges\s+for\s+\d{3}-\d{3}-\d{4}', re.IGNORECASE)

    def initial_page_data(self,data):
        print(data)

    def extract_all(self):
        matching_pages = []
        with pdfplumber.open(self.path) as pdf:
            page1 = pdf.pages[0]
            self.initial_page_data(page1.extract_text().splitlines())
            # for i, page in enumerate(pdf.pages):
            #     text = page.extract_text()
            #     if text and self.details_key_pattern.search(text):
            #         matching_pages.append({i:text})
        # print(matching_pages[10])
        print(len(matching_pages))
    



path = "Bills/media/ViewUploadedBills/mob_1899_34212553900001_07152025.pdf"
print(path)
obj = Verizon2(path)
obj.extract_all()