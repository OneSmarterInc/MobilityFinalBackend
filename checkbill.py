
import pdfplumber
def prove_bill_ID(bill_path,vendor_name):
    # Open the PDF file
    Lines = []
    print(bill_path, vendor_name)
    with pdfplumber.open(bill_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if i == 0:
                page_text = page.extract_text()
                lines = page_text.split('\n')
                Lines.extend(lines)
            else:
                break
    
    for line in Lines:
        if (vendor_name == "AT&T") and ('AT&T' in line):
            print(line, vendor_name)
            return True
        elif (vendor_name == "T_mobile") and ('T-MOBILE'.lower() in line.lower()):
            return True
        elif (vendor_name == "Verizon") and 'verizon' in line.lower():
            print(line, vendor_name)
            return True
    return False

def check_tmobile_type(pdf_path):
        print("def check_tmobile_type")
        Lines = []
        with pdfplumber.open(pdf_path) as pdf:
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

import re
def checkVerizon(pages,org):
    page = pages[0]
    width = page.width
    height = page.height

    left_side_bbox = (0, 0, width * 0.4, height / 4)
    left_side_bottom_half = page.within_bbox(left_side_bbox)
    address = left_side_bottom_half.extract_text().split("KEYLINE")
    billing = address[1].strip().split("\n")[1:]
    billing_name = billing[0] if billing else None

    bottom_half_bbox = (0, height / 2, width, height)
    bottom_half = page.within_bbox(bottom_half_bbox)
    bottom_text = bottom_half.extract_text()
    account_number_match = re.search(r"Account Number ([\d\-]+)", bottom_text)
    account_number = account_number_match.group(1) if account_number_match else None
    bill_date_pattern = re.search(r"(Bill Date)\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", bottom_text)
    bill_date = bill_date_pattern.group(2).replace(",","") if bill_date_pattern else None
    return account_number, bill_date,billing_name