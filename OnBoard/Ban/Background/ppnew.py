import pdfplumber
from Scripts.Verizon1 import VerizonClass
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