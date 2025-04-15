
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