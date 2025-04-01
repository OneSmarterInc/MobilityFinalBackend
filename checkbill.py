
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