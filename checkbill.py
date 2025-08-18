
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

def checkVerizon(pages):
    try:
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
    except:
        return None, None, None

def checkAtt(pages):
    try:
        page = pages[0]
        width = page.width
        height = page.height
        x0 = width/2
        top_half_bbox = (0, 0, width, height / 4)
        bottom_half_bbox = (0, height / 1.5, width, height)
        top_half = page.within_bbox(top_half_bbox)
        bottom_half = page.within_bbox(bottom_half_bbox)
        words = bottom_half.extract_words(extra_attrs=["size", "fontname"])
        for i in range(len(words) - 1):
            if "pay" in words[i]['text'].lower():
                x0 = words[i]['x0']
                break
        top_text = top_half.extract_text()

        account_number_match = re.search(r"Account Number: ([\d\-]+)", top_text)
        account_number = account_number_match.group(1) if account_number_match else None


        bill_date_match = re.search(r"Issue Date:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", top_text)
        bill_date = bill_date_match.group(1).replace(",","") if bill_date_match else None


        bottom_left_box = (0, height / 1.5, x0-10, height-100)
        bottom_left = page.within_bbox(bottom_left_box)

        bottom_left_text = bottom_left.extract_text()
        bottom_left_text = re.sub(r"(\d{5}-\d{4}).*$", r"\1", bottom_left_text, flags=re.DOTALL)

        billing_name = None
        lines = bottom_left_text.split("\n")
        for i,line in enumerate(lines):
            if "attn" in line.lower():
                billing_name = lines[i-1].strip()
        if not billing_name:
            billing_name = lines[-3].strip()
        
        return account_number, bill_date, billing_name
    except:
        return None, None, None
def checkTmobile1(pages):
    pass
def checkTmobile2(pages):
    try:
        page = pages[0]
        width = page.width
        height = page.height
        top_half_bbox = (0, 0, width, height / 2)
        top_half = page.within_bbox(top_half_bbox)
        top_text = top_half.extract_text()
        billing_name = None
        topLines = top_text.splitlines()
        for i,line in enumerate(topLines):
            if (("account" and "invoice") in line.lower()):
                nxtLine = topLines[i+1]
                items = nxtLine.strip().split(" ")[:-3]
                account_number = items[-2]
                bill_period = " ".join(items[:-2])
                bill_date = bill_period.split("-")[1].strip().replace(",","")
            if "welcome" in line.lower():
                line = line.split("Welcome")[1]
                nxtLine = topLines[i+1]
                if not "your" in nxtLine.lower():
                    billing_name = f'{line} {nxtLine}'.strip().replace(",","")
                else:
                    billing_name = f'{line}'.strip().replace(",","")

        return account_number, bill_date, billing_name
    except:
        return None, None, None