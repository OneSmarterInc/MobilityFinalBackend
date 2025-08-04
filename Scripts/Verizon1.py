import pandas as pd
import pdfplumber,re,time

class Verizon1:
    def __init__(self,path):
        self.path = path
        self.account_number = None
        self.invoice_number = None
        self.bill_date = None
        self.due_date = None
        self.bill_period = None
        self.total_amount = None
        self.remmitance = None
        self.billing = {}
        self.key = None
        self.unique_key_pattern = re.compile(r'(?:\d{3}[-.]){2}\d{4}\s+[A-Za-z]+\s+[A-Za-z]+\s+\d+\s+(?:\$\d+(?:\.\d{2})?|--)', re.IGNORECASE)
        self.details_key_pattern = re.compile(r"(?=.*\bTotal\b)(?=.*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", re.IGNORECASE)

    def get_account_number(self):
        return self.account_number

    def get_invoice_number(self):
        return self.invoice_number
    
    def get_bill_date(self):
        return self.bill_date
    
    def get_due_date(self):
        return self.due_date
    
    def get_net_amount(self):
        return self.total_amount
    
    def get_billing_info(self):
        return self.billing

    def get_remmit_info(self):
        return self.remmitance
    
    def initial_page_data(self,pages):
        page = pages[0]

        width = page.width
        height = page.height

        bottom_half_bbox = (0, height / 2, width, height)

        bottom_half = page.within_bbox(bottom_half_bbox)
        bottom_text = bottom_half.extract_text()

        invoice_number_match = re.search(r"Invoice Number (\d+)", bottom_text)
        self.invoice_number = invoice_number_match.group(1) if invoice_number_match else None

        account_number_match = re.search(r"Account Number ([\d\-]+)", bottom_text)
        self.account_number = account_number_match.group(1) if account_number_match else None

        amount_match = re.search(r"\$[\d,]+\.\d{2}", bottom_text)
        self.total_amount = amount_match.group() if amount_match else None

        bill_date_pattern = re.search(r"(Bill Date)\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", bottom_text)
        self.bill_date = bill_date_pattern.group(2).replace(",","") if bill_date_pattern else None

        due_date_pattern = re.search(r"(Total Amount Due)(?: by ([A-Za-z]+\s+\d{1,2},\s+\d{4}))?", bottom_text)
        self.due_date = due_date_pattern.group(2) if due_date_pattern.group(2) else "Past"
        self.due_date = self.due_date.replace(",","") if not "Past" in self.due_date else self.due_date
        

        left_side_bbox = (0, 0, width * 0.4, height / 4)
        left_side_bottom_half = page.within_bbox(left_side_bbox)
        address = left_side_bottom_half.extract_text().split("KEYLINE")
        self.remmitance = address[0].replace("\n"," ").strip()
        billing = address[1].strip().split("\n")[1:]
        self.billing["name"] = billing[0]
        self.billing["address"] = " ".join(billing[1:])
        com = {
            "Account Number": self.account_number,
            "Invoice Number": self.invoice_number,
            "Total Amount": self.total_amount,
            "Bill Date": self.bill_date,
            "Due Date": self.due_date,
            "Billing Info": self.billing,
            "Remittance Info": self.remmitance
        }
        print(com)

    def unique_data(self,pages):
        all_lines = []
        for page in pages:
            data = page.extract_text()
            pattern = r'^(?:\d{3}[-.]){2}\d{4}.*(?:--|\$\d+(?:\.\d{2})?)'
            matching_lines = [line for line in data.splitlines() if re.search(pattern, line.strip())]
            all_lines += matching_lines
        print(len(all_lines))
        for line in all_lines:
            print(line)
    def baseline_data(self,pages):
        pass

    def extract_all(self):
        matching_page_basic = []
        matching_pages_unique = []
        matching_pages_baseline = []
        with pdfplumber.open(self.path) as pdf:
            extraction_start_time = time.perf_counter()
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not self.key and (("account" and "invoice") in text.lower()):
                    if not matching_page_basic:
                        matching_page_basic.append(page)
                if text and self.unique_key_pattern.search(text):
                    matching_pages_unique.append(page)
                if text and self.details_key_pattern.search(text):
                    matching_pages_baseline.append(page)
            extraction_finish_time = time.perf_counter()
            print(f"Extraction time: {extraction_finish_time-extraction_start_time:.2f} seconds")

            process_start_time = time.perf_counter()
            self.initial_page_data(matching_page_basic)
            self.unique_data(matching_pages_unique)
            self.baseline_data(matching_pages_baseline)
            process_finish_time = time.perf_counter()
            print(f"Process Execution time: {process_finish_time-process_start_time:.2f} seconds")
                            
    



path = "Bills/media/ViewUploadedBills/Verizon.pdf"
obj = Verizon1(path)
obj.extract_all()