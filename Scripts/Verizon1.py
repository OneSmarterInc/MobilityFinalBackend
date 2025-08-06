import pandas as pd
import pdfplumber,re,time

class VerizonClass:
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
        self.planSide = None
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
        return com        

    def unique_data(self,pages):
        all_lines = []
        lines_data = []
        for page in pages:
            data = page.extract_text()
            pattern = r'^(?:\d{3}[-.]){2}\d{4}.*(?:--|\$\d+(?:\.\d{2})?)'
            matching_lines = [line for line in data.splitlines() if re.search(pattern, line.strip())]
            all_lines += matching_lines
        for line in all_lines:
            line = line.split()
            lines_data.append({
                "Wireless Number": line[0],
                "Username": " ".join(line[1:-14]),
                "Page": line[-14],
                "Data Roaming": line[-1],
                "Message Roaming": line[-2],
                "Voice Roaming": line[-3],
                "Data Usage": line[-4],
                "Message Usage":line[-5],
                "Voice Plan Usage":line[-6],
                "Total Charges": line[-7],
                "Third Party Charges (includes Tax)": line[-8],
                "Taxes, Governmental Surcharges and Fees": line[-9],
                "Surcharges and Other Charges and Credits": line[-10],
                "Equipment Charges": line[-11],
                "Usage and Purchase Charges":line[-12],
                "Monthly Charges": line[-13],
            })
        unique_df = pd.DataFrame(lines_data).replace("--","NA")
        return unique_df
    def baseline_data(self,pages,unique_df=None):
        final_data = []
        all_charges_data = {}
        all_plan_data = {}
        page = pages[0]
        self.x0 = page.width / 2
        words = page.extract_words(extra_attrs=["size", "fontname"])

        for i in range(len(words) - 1):
            if "your" in words[i]['text'].lower():
                self.x0 = words[i]['x0']
                break
        if self.x0 < page.width/2:
            self.planSide = "left"
        elif self.x0 > page.width/2:
            self.planSide = "right"
        
        # now page break
        if self.planSide == "left":
            planBox = (0, 0, self.x0+170, page.height)
            chargesBox = (self.x0+175, 0, page.width, page.height)
        elif self.planSide == "right":
            planBox = (self.x0-10, 0, page.width, page.height)
            chargesBox = (0, 0, self.x0-10, page.height)
        pattern =r"(.+?)\s+(-?\$?(?:\d+\.\d{2}|\.\d{2}))"
        
        for page in pages:
            
            plan = page.within_bbox(planBox)
            plan_text = plan.extract_text()
            match = re.search(r'Plan\s*(.*)', plan_text, flags=re.DOTALL)
            plan_text = match.group(1) if match else plan_text

            charges = page.within_bbox(chargesBox)
            charges_text = charges.extract_text()
            charges_text = re.sub(r"\d{2}/\d{2}\s*-\s*\d{2}/\d{2}", "", charges_text)
            wn_match = re.findall(r"\d{3}[-.]\d{3}[-.]\d{4}", charges_text)
            if wn_match:
                wn = wn_match[0]
                all_charges_data[wn] = charges_text
                all_plan_data[wn] = plan_text
        self.category = None
        for wn, chargesText in all_charges_data.items():
            lines = [line for line in chargesText.splitlines() if "total" not in line.lower()]
            lines = [line for line in lines if "usage" not in line.lower()]
            for line in lines:

                if "charges" in line.lower():
                    matches = re.findall(pattern, line)
                    if matches:
                        for cat, amount in matches:
                            self.category = cat.strip()                                    
                    else:
                        self.category = line.strip()
                else:
                    matches = re.findall(pattern, line)
                    if matches:
                        final_data.append({
                            "Wireless Number": wn,
                            "Item Category": self.category,
                            "Item Description":matches[0][0].strip(),
                            "Charges":matches[0][1].strip()
                        })
        # for wn, planText in all_plan_data.items():
        #     lines = planText.splitlines()
        #     for line in lines:
        #         print(line)

        df = pd.DataFrame(final_data)
        if unique_df is not None:
            baseline_df = pd.merge(unique_df, df, on="Wireless Number")  
        else:
            baseline_df = df
        
        return baseline_df
        

    def extract_all(self):
        matching_page_basic = []
        matching_pages_unique = []
        matching_pages_baseline = []
        with pdfplumber.open(self.path) as pdf:
            extraction_start_time = time.perf_counter()
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not self.key and (("account" and "invoice" and "keyline") in text.lower()):
                    if not matching_page_basic:
                        matching_page_basic.append(page)
                if text and self.unique_key_pattern.search(text):
                    matching_pages_unique.append(page)
                if text and self.details_key_pattern.search(text):
                    # if matching_pages_baseline:
                    #     break
                    matching_pages_baseline.append(page)
            extraction_finish_time = time.perf_counter()
            extraction_time = extraction_finish_time - extraction_start_time
            print(f"Extraction time: {extraction_time} seconds")

            process_start_time = time.perf_counter()
            basic_data = self.initial_page_data(matching_page_basic)
            unique_df = self.unique_data(matching_pages_unique)
            baseline_df = self.baseline_data(matching_pages_baseline, unique_df=unique_df)
            process_finish_time = time.perf_counter()
            process_time = process_finish_time - process_start_time
            print(f"Processing time: {process_time} seconds")
            return basic_data, unique_df, baseline_df, f"{(extraction_time + process_time):.2f}"



# path = "Bills/media/ViewUploadedBills/Verizon.pdf"
# obj = VerizonClass(path)
# basic_data, unique_df, baseline_df,total_time = obj.extract_all()
# print(basic_data)
# print(unique_df.head(3))
# print(baseline_df.head(3))
# print(total_time)
# unique_df.to_csv(path.replace(".pdf","_unique.csv"))
# baseline_df.to_csv(path.replace(".pdf","_baseline.csv"))
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class ProcessPdf:
    def __init__(self, buffer_data,instance=None):
        self.instance = instance
        self.buffer_data = buffer_data
        self.pdf_path = self.buffer_data.get('pdf_path')
        self.company_name = self.buffer_data.get('company_name')
        self.vendor_name = self.buffer_data.get('vendor_name')
        self.pdf_filename = self.buffer_data.get('pdf_filename')
        self.month = self.buffer_data.get('month')
        self.entry_type = self.buffer_data.get('entry_type')
        self.baseline_check = str(self.buffer_data.get('baseline_check')).lower() == 'true'
        self.location = self.buffer_data.get('location')
        self.master_account = self.buffer_data.get('master_account')
        self.year = self.buffer_data.get('year')
        self.types = self.buffer_data.get('types')
        self.email = self.buffer_data.get('user_email')
        self.sub_company = self.buffer_data.get('sub_company')
        self.t_mobile_type = self.check_tmobile_type() if 'mobile' in str(self.vendor_name).lower() else 0

        logger.info(f'Processing PDF from buffer: {self.pdf_path}, {self.company_name}, {self.vendor_name}, {self.pdf_filename}')

        self.bill_date = None
        self.net_amount = 0
        self.check = True
        self.account_number = None
        self.billing_address = {}

    def check_tmobile_type(self):
        print("def check_tmobile_type")
        Lines = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                if i == 0:
                    page_text = page.extract_text()
                    lines = page_text.split('\n')
                    Lines.extend(lines)
                else:
                    break

        if 'Bill period Account Invoice Page' in Lines[0]:
            print("Type2 : Bill period Account Invoice Page")
            return 2
        elif 'Your Statement' in Lines[0]:
            print("Type1 : Your Statement")
            return 1
        else:
            return 0

    def start_process(self):
        obj = VerizonClass(self.pdf_path)
        basic_data, unique_df, baseline_df,total_time = obj.extract_all()
        print(basic_data)
        print(unique_df.head(3))
        print(baseline_df.head(3))
        print(total_time)

tst = sample_buffer_data = {
    "pdf_path": "Bills/media/ViewUploadedBills/Verizon.pdf",
    "company_name": "SimpleTek",
    "vendor_name": "Verizon",
    "pdf_filename": "Verizon.pdf",
    "month": None,
    "entry_type": "Base Account",
    "baseline_check": True,
    "location": None,
    "master_account": None,
    "year": None,
    "types": None,
    "user_email": "user@example.com",
    "sub_company": "BABW"
}

obj = ProcessPdf(tst,instance=None)
obj.start_process()