# Verizon Bill Processor by SAW
import os
import pdfplumber
import pandas as pd
import re



class Verizon:
    def __init__(self, in_path):
        self.input_path = in_path
        self.data_new = None
        print("started")
        
        self.list1 = []
        self.lines = []

    def top_part_dims(self, page, top_height):
        return 0, 0, page.width, top_height

    def left_part_dims(self, page, top_height):
        return 0, top_height, page.width * 0.35, page.height

    def right_part_dims(self, page, top_height):
        return page.width * 0.35, top_height, page.width, page.height

    def extract_text_from_part(self, page, part_dims):
        if part_dims is None:
            return None
        return page.crop(part_dims).extract_text()

    def new_text(self):
        Data = []
        with pdfplumber.open(self.input_path) as pdf:
            pages = len(pdf.pages)

        for num_page in range(pages):
            with pdfplumber.open(self.input_path) as pdf:
                page = pdf.pages[num_page]    
                page_text = page.extract_text()
                if "Monthly Charges" in page_text:
                    Lines = page_text.split("\n")
                    for line in Lines:
                        Data.append(line)
        return Data

    def margin_text(self,page):
                print(page)
                margin_left = page.bbox[0] + 510
                margin_top = page.bbox[1]
                margin_right = page.bbox[2]
                margin_bottom = page.bbox[3]
                page = page.crop((margin_left, margin_top, margin_right, margin_bottom))
                text = page.extract_text()
                Lines = text.split("\n")
                for line in Lines:
                    match = re.search(
                        r'(?:.*?(\$?\d+(?:\.\d+)?)|--)$',
                        line)
                    if match:
                        self.list1.append(line)

    def extract_text_from_pdf(self):
        
        summary_pattern = re.compile(r'Summary for (.+?): (\d{3}-\d{3}-\d{4})')
        detail_pattern = re.compile(r'Detail for (.+?): (\d{3}-\d{3}-\d{4})')
        data_new = ''
        with pdfplumber.open(self.input_path) as pdf:
            no_of_pages = len(pdf.pages)

        for num_page in range(no_of_pages):
            with pdfplumber.open(self.input_path) as pdf:
                page = pdf.pages[num_page]
                self.margin_text(page)
                print("back to logic ")
                page_text = page.extract_text()
                summary_match = summary_pattern.search(page_text)
                detail_match = detail_pattern.search(page_text)
                if summary_match or detail_match:
                   if summary_match:
                       top_height = 0.15 * float(page.height)
                       top_part_text = self.extract_text_from_part(page, self.top_part_dims(page, top_height))
                       left_part_text = self.extract_text_from_part(page, self.left_part_dims(page, top_height))
                       right_part_text = self.extract_text_from_part(page, self.right_part_dims(page, top_height))
                       data_new += '\n' + top_part_text
                       data_new += '\n' + left_part_text
                       data_new += '\n' + right_part_text
                   else:
                       detail_line_text = [line for line in page_text.split('\n') if detail_pattern.search(line)][0]
                       top_line = page_text.split('\n').index(detail_line_text)
                       top_height = top_line * float(page.height) / len(page_text.split('\n'))
                       top_part_text = self.extract_text_from_part(page, (0, 0, page.width, top_height))
                       data_new += '\n' + top_part_text
                else:
                    data_new += page_text + '\n'
        self.data_new = data_new
        return data_new

    def part_1(self):
        Lines = []
        data_fun = self.extract_text_from_pdf()
        lines = data_fun.split('\n')
        for line in lines:
            if line.startswith('Account Charges (pg.2)'):
                items = line.split()
                items[1] = items[0] + ' ' + items[1]
                items[0] = '--'
                del items[2]
                Lines.append({'Wireless Number': 'NA' if items[0] == '--' else items[0],
                              'User Name': 'NA' if items[1] == '--' else items[1],
                              'Account Charges and Credits': 'NA' if items[2] == '--' else items[2], 'Page Number': '2',
                              'Monthly Charges': 'NA' if items[3] == '--' else items[3],
                              'Usage and Purchase Charges': 'NA' if items[4] == '--' else items[4],
                              'Equipment Charges': 'NA' if items[5] == '--' else items[5],
                              'Surcharges and Other Charges and Credits': 'NA' if items[6] == '--' else items[6],
                              'Taxes, Governmental Surcharges and Fees': 'NA' if items[7] == '--' else items[7],
                              'Third-Party Charges (includes Tax)': 'NA' if items[8] == '--' else items[8],
                              'Total Charges': 'NA' if items[9] == '--' else items[9], 'Voice Plan Usage': 'NA',
                              'Messaging Usage': 'NA', 'Data Usage': 'NA', 'Voice Roaming': 'NA',
                              'Messaging Roaming': 'NA',
                              'Data Roaming': 'NA'})
            elif line.startswith('Account Plan and Charges** (pg.2)'):
                items = line.split()
                items[1] = items[0] + ' ' + items[1] + ' ' + items[2] + ' ' + items[3]
                items[0] = '--'
                for i in range(3):
                    del items[2]
                Lines.append({'Wireless Number': 'NA' if items[0] == '--' else items[0],
                              'User Name': 'NA' if items[1] == '--' else items[1],
                              'Account Charges and Credits': 'NA' if items[2] == '--' else items[2], 'Page Number': '2',
                              'Monthly Charges': 'NA' if items[3] == '--' else items[3],
                              'Usage and Purchase Charges': 'NA' if items[4] == '--' else items[4],
                              'Equipment Charges': 'NA' if items[5] == '--' else items[5],
                              'Surcharges and Other Charges and Credits': 'NA' if items[6] == '--' else items[6],
                              'Taxes, Governmental Surcharges and Fees': 'NA' if items[7] == '--' else items[7],
                              'Third-Party Charges (includes Tax)': 'NA' if items[8] == '--' else items[8],
                              'Total Charges': 'NA' if items[9] == '--' else items[9], 'Voice Plan Usage': 'NA',
                              'Messaging Usage': 'NA', 'Data Usage': 'NA', 'Voice Roaming': 'NA',
                              'Messaging Roaming': 'NA',
                              'Data Roaming': 'NA'})

            match = re.search(
                r'(\d{3}-\d{3}-\d{4}) (.+?|.+? \b\d+\b) (\d+|\d+\,\d+|\--) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$['
                r'0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\--) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,'
                r']+\.\d+|\--) (\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\--) ('
                r'\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\--) ('
                r'\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\--) ('
                r'\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\--) ('
                r'\-\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+|\--) (\d+|\d+\,'
                r'\d+|\--) (\d+|\d+\,\d+|\--) (\d+\.\d+GB|\.\d+GB||\--) (\d+|\d+\,\d+|\--) (\d+|\d+\,\d+|\--) (\d+|\d+\,'
                r'\d+|\--)',
                line)
            if match:
                Lines.append({'Wireless Number': 'NA' if match.group(1) == '--' else match.group(1),
                              'User Name': 'NA' if match.group(2) == '--' else match.group(2),
                              'Account Charges and Credits': 'NA',
                              'Page Number': 'NA' if match.group(3) == '--' else match.group(3),
                              'Monthly Charges': 'NA' if match.group(4) == '--' else match.group(4),
                              'Usage and Purchase Charges': 'NA' if match.group(5) == '--' else match.group(5),
                              'Equipment Charges': 'NA' if match.group(6) == '--' else match.group(6),
                              'Surcharges and Other Charges and Credits': 'NA' if match.group(
                                  7) == '--' else match.group(
                                  7),
                              'Taxes, Governmental Surcharges and Fees': 'NA' if match.group(
                                  8) == '--' else match.group(8),
                              'Third-Party Charges (includes Tax)': 'NA' if match.group(9) == '--' else match.group(9),
                              'Total Charges': 'NA' if match.group(10) == '--' else match.group(10),
                              'Voice Plan Usage': 'NA' if match.group(11) == '--' else match.group(11),
                              'Messaging Usage': 'NA' if match.group(12) == '--' else match.group(12),
                              'Data Usage': 'NA' if match.group(13) == '--' else match.group(13),
                              'Voice Roaming': 'NA' if match.group(14) == '--' else match.group(14),
                              'Messaging Roaming': 'NA' if match.group(15) == '--' else match.group(15),
                              'Data Roaming': 'NA' if match.group(16) == '--' else match.group(16)})
        self.lines = Lines
        return Lines

    def part_2(self):
        result = []
        current_section = None
        current_sections = None
        data = self.extract_text_from_pdf()
        lines = data.split('\n')
        check = 0
        start = 0
        list_not = ['Usage and Purchase Charges', 'Voice', 'Messaging', 'Data', 'International']
        date = ""
        account = ""
        name = ""
        number = ""
        status = ""
        center = ""
        plan = ""
        invoice = ""
        for i, line in enumerate(lines):
            match1 = re.search(r'Bill Date (.+? \d{4})', line)
            match2 = re.search(r'Account Number (\d{9}-\d{5})', line)
            match3 = re.search(r'Invoice Number (\d{10})', line)
            if match1:
                date = match1.group(1)
            if match2:
                account = match2.group(1)
            if match3:
                invoice = match3.group(1)
            if line.startswith('Account Charges (pg.2)'):
                items = line.split()
                items[1] = items[0] + ' ' + items[1]
                items[0] = '--'
                del items[2]
                result.append({
                    'Foundation Account': 'NA',
                    'Account Number': account,
                    'Group Number': 'NA',
                    'User Name': 'NA' if items[1] == '--' else items[1],
                    'Wireless Number': 'NA',
                    'User Email': 'NA',
                    'Status': 'Inactive',
                    'Cost Center': 'NA',
                    'Account Charges and Credits': 'NA' if items[2] == '--' else items[2],
                    'Plans': 'NA',
                    'Item Category': 'NA',
                    'Item Type': 'NA',
                    'Item Description': 'NA',
                    'Share Description': 'NA',
                    'Share Voice': 'NA',
                    'Share Messaging': 'NA',
                    'Share Data': 'NA',
                    'Allowance': 'NA',
                    'Used': 'NA',
                    'Billable': 'NA',
                    'Charges': '0' if items[9] == '--' else items[9],
                    'Order Details': 'NA',
                    'Bill Cycle Date': date,
                    'Invoice Number': invoice
                }
                )
                break
            elif line.startswith('Account Plan and Charges** (pg.2)'):
                items = line.split()
                items[1] = items[0] + ' ' + items[1] + ' ' + items[2] + ' ' + items[3]
                items[0] = '--'
                for i in range(3):
                    del items[2]
                result.append({
                    'Foundation Account': 'NA',
                    'Account Number': account,
                    'Group Number': 'NA',
                    'User Name': 'NA' if items[1] == '--' else items[1],
                    'Wireless Number': 'NA',
                    'User Email': 'NA',
                    'Status': 'Inactive',
                    'Cost Center': 'NA',
                    'Account Charges and Credits': 'NA' if items[2] == '--' else items[2],
                    'Plans': 'NA',
                    'Item Category': 'NA',
                    'Item Type': 'NA',
                    'Item Description': 'NA',
                    'Share Description': 'NA',
                    'Share Voice': 'NA',
                    'Share Messaging': 'NA',
                    'Share Data': 'NA',
                    'Allowance': 'NA',
                    'Used': 'NA',
                    'Billable': 'NA',
                    'Charges': '0' if items[9] == '--' else items[9],
                    'Order Details': 'NA',
                    'Bill Cycle Date': date,
                    'Invoice Number': invoice
                })
                break
        for i, line in enumerate(lines):
            match = re.search(r'Summary for (.+?): (\d{3}-\d{3}-\d{4})', line)
            if match:
                start = 1
                name = match.group(1)
                number = match.group(2)
                center = lines[i + 1]
                if center == 'Your Plan':
                    center = 'NA'
                for item in self.lines:
                    if item.get('Wireless Number') == number and item.get('User Name') == name:
                        status = float(item.get('Monthly Charges').replace('$', ''))
                        status = 'Active' if status > 0 else 'Inactive'
                        break
            if line.startswith('Your Plan'):
                match = re.search(r'(.*GB$|.*MB$)', lines[i + 1])
                if match:
                    plan = lines[i + 1]
                match = re.search(r'(.*GB$|.*MB$)', lines[i + 2])
                if match:
                    plan = lines[i + 2]
                else:
                    plan = lines[i + 1]
            if start != 0:
                if line.startswith('Monthly Charges'):
                    current_section = 'Monthly Charges'
                elif line.startswith('EquipmentCharges'):
                    current_section = 'Equipment Charges'
                    check = 1
                elif line.startswith('Usage and Purchase Charges'):
                    current_section = 'Usage and Purchase Charges'
                elif line.startswith('Surcharges') or line.startswith('Surcharges+'):
                    current_section = 'Surcharges'
                elif line.startswith('OtherChargesandCredits'):
                    current_section = 'Other Charges and Credits'
                elif line.startswith('Taxes, Governmental Surcharges and Fees') or line.startswith(
                        'Taxes, Governmental Surcharges and Fees+'):
                    current_section = 'Taxes, Governmental Surcharges and Fees'
                elif line.startswith('Total Current Charges for'):
                    current_section = None

                match = re.search(
                    r'(.+? \d+\.\d+ .+?|.+?) (--|\.\d+|\d+\.\d+|\d+\,\d+\.\d+|\-\.\d+|\-\d+\.\d+|\-\d+\,\d+\.\d+)\s*$',
                    line)

                if match and (current_section not in list_not and current_section != None) and (
                        match.group(2) in self.list1 and 'Due' not in line):
                    if check == 1:
                        check = 0
                        result.append(
                            {'Foundation Account': 'NA', 'Account Number': account, 'Group Number': 'NA',
                             'User Name': name,
                             'Wireless Number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': current_section,
                             'Item Type': 'NA', 'Item Description': match.group(1), 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': 'NA' if match.group(2) == "--" else match.group(2),
                             'Order Details': 'NA',
                             'Bill Cycle Date': date, 'Invoice Number': invoice})
                    else:
                        result.append(
                            {'Foundation Account': 'NA', 'Account Number': account, 'Group Number': 'NA',
                             'User Name': name,
                             'Wireless Number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                             'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': current_section,
                             'Item Type': 'NA', 'Item Description': match.group(1), 'Share Description': 'NA',
                             'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                             'Used': 'NA', 'Billable': 'NA',
                             'Charges': '0' if match.group(2) == "--" else match.group(2),
                             'Order Details': 'NA',
                             'Bill Cycle Date': date, 'Invoice Number': invoice})

                if current_section == 'Usage and Purchase Charges':
                    if re.search(r"Voice Allowance Used Billable Cost", line):
                        current_sections = 'Voice'
                    elif re.search(r"Messaging Allowance Used Billable Cost", line):
                        current_sections = 'Messaging'
                    elif re.search(r"Data Allowance Used Billable Cost", line):
                        current_sections = 'Data'
                    elif line.startswith('International Allowance Used Billable Cost'):
                        current_sections = 'International'
                    if "unlimited" not in line and ('Calling' in line) or (
                            'Gigabyte' in line and 'shared' not in lines[i + 1]) or (
                            "Shared" in line and "unlimited" not in line):
                        if "Shared" in line and "unlimited" not in line:
                            words = line.split()
                            words.insert(2, "NA")
                            line = ' '.join(words)
                        else:
                            words = line.split()
                            words.insert(3, "NA")
                            line = ' '.join(words)
                    match = re.search(
                        r'(.+?) (minutes|messages|gigabytes) (unlimited|\.\d+|\d+\.\d+|\d+\,\d+\.\d+|\-\.\d+|\-\d+\.\d+|\-\d+\,\d+\.\d+|\--|NA) (.+)',
                        line)
                    match_I = re.search(
                        r'(International\s*Minutes)\s*(minutes|messages)\s*(\d+)\s*(\d+)\s*(-?\$\d{1,3}(?:,\d{3})*\.\d+)',
                        line)
                    if current_sections == "International" or match_I:
                        if match:
                            result.append({'Foundation Account': 'NA', 'Account Number': account, 'Group Number': 'NA',
                                           'User Name': name, 'Wireless Number': number, 'User Email': 'NA',
                                           'Status': status, 'Cost Center': center, 'Account Charges and Credits': 'NA',
                                           'Plans': plan, 'Item Category': current_sections,
                                           'Item Type': match.group(2),
                                           'Item Description': match.group(1), 'Share Description': 'NA',
                                           'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA',
                                           'Allowance': match.group(3), 'Used': match.group(4),
                                           'Billable': match.group(5),
                                           'Charges': '0' if match.group(6) == "--" or " " else match.group(6),
                                           'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})
                    elif match and current_sections != 'International':
                        temp = 0
                        if current_sections == 'Data':
                            try:
                                value = float(match.group(3))
                                if isinstance(value, float):
                                    allowance = match.group(3) + '(shared)'
                                    temp = 1
                            except ValueError:
                                temp = 0
                        split_result = match.group(4).split()
                        result.append({'Foundation Account': 'NA',
                                       'Account Number': account,
                                       'Group Number': 'NA',
                                       'User Name': name,
                                       'Wireless Number': number,
                                       'User Email': 'NA',
                                       'Status': status,
                                       'Cost Center': center,
                                       'Account Charges and Credits': 'NA',
                                       'Plans': plan,
                                       'Item Category': current_sections,
                                       'Item Type': match.group(2),
                                       'Item Description': match.group(1),
                                       'Share Description': 'NA' if temp == 0 else 'Shared Usage',
                                       'Share Voice': 'NA',
                                       'Share Messaging': 'NA',
                                       'Share Data': 'NA' if temp == 0 else match.group(3),
                                       'Allowance': match.group(3) if temp == 0 else allowance,
                                       'Used': '0' if match.group(4).split()[0] == '--' else match.group(4).split()[0],
                                       'Billable': '0' if match.group(4).split()[1] == '--' else match.group(4).split()[
                                           1],
                                        
                                        'Charges': '0' if len(split_result) < 3 or split_result[2] == '--' else split_result[2],

                                       'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})


                    else:
                        match = re.search(r' (--|\.\d+|\d+\.\d+|\d+\,\d+\.\d+|\-\.\d+|\-\d+\.\d+|\-\d+\,\d+\.\d+)\s*$',
                                          line)

                        if match and (match.group(1) in self.list1 and 'Due' not in line):
                            result.append({'Foundation Account': 'NA', 'Account Number': account, 'Group Number': 'NA',
                                           'User Name': name, 'Wireless Number': number, 'User Email': 'NA',
                                           'Status': status, 'Cost Center': center, 'Account Charges and Credits': 'NA',
                                           'Plans': plan, 'Item Category': current_sections, 'Item Type': 'NA',
                                           'Item Description': match.group(1), 'Share Description': 'NA',
                                           'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA',
                                           'Allowance': 'NA', 'Used': 'NA', 'Billable': 'NA',
                                           'Charges': '0' if match.group(1) == "--" else match.group(1),
                                           'Order Details': 'NA', 'Bill Cycle Date': date, 'Invoice Number': invoice})

                match = re.search(r' (\--\$\d+\.\d+|\-\$\.\d+|\$\d+\.\d+|\$\.\d+|\$[0-9,]+\.\d+|\-\$[0-9,]+\.\d+)\s*$',
                                  line)

                if line.startswith('TotalInternational') or line.startswith('TotalUsageandPurchaseCharges'):
                    current_section = None
                    current_sections = None
                elif match and current_sections == 'International' and (
                        match.group(1) in self.list1 and 'Due' not in line):
                    result.append(
                        {'Foundation Account': 'NA', 'Account Number': account, 'Group Number': 'NA', 'User Name': name,
                         'Wireless Number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                         'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': current_sections,
                         'Item Type': 'NA', 'Item Description': match.group(1), 'Share Description': 'NA',
                         'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                         'Used': 'NA',
                         'Billable': 'NA', 'Charges': '0' if match.group(1) == "--" else match.group(1),
                         'Order Details': 'NA', 'Bill Cycle Date': date,
                         'Invoice Number': invoice})
                elif line.startswith("International Minutes") or line.startswith("International Messages"):
                    cost = line.split()[-1]
                    billable = line.split()[-2]
                    used = line.split()[-3]
                    itype = line.split()[-4]
                    description = line.split()[:-4]
                    description = " ".join(description)
                    result.append(
                        {'Foundation Account': 'NA', 'Account Number': account, 'Group Number': 'NA', 'User Name': name,
                         'Wireless Number': number, 'User Email': 'NA', 'Status': status, 'Cost Center': center,
                         'Account Charges and Credits': 'NA', 'Plans': plan, 'Item Category': current_sections,
                         'Item Type': itype, 'Item Description': description, 'Share Description': 'NA',
                         'Share Voice': 'NA', 'Share Messaging': 'NA', 'Share Data': 'NA', 'Allowance': 'NA',
                         'Used': used,
                         'Billable': billable, 'Charges': '0' if (cost == "--" or " ") else cost,
                         'Order Details': 'NA', 'Bill Cycle Date': date,
                         'Invoice Number': invoice})

        return result

    def to_csv(self, data_list, output_path):
        try:
            df = pd.DataFrame(data_list)
            print(df)
            df.to_csv(output_path, index=False)
            
            print(f"csv file created! to path {output_path}")
        except Exception as e:
            print(e)
            return None

import os

def process_all(pdf_file_path):
    print("entered")
    try:

        # Process part 1 (sum)
        data_list = Verizon(pdf_file_path)
        data_list2 = data_list
        y = data_list.part_1()
        details_file_path = pdf_file_path.replace(".pdf", "_summary.csv")
        data_list.to_csv(y, details_file_path)
        
        # Process part 2 (det)
        
        x = data_list2.part_2()
        summary_file_path = pdf_file_path.replace(".pdf", "_details.csv")
        data_list.to_csv(x, summary_file_path)

        # Save processed files details
        
    except Exception as e:
        print(e)

pdf_file_path= 'Bills/media/ViewUploadedBills/Verizon.pdf'
data_list = Verizon(pdf_file_path)
data_list2 = data_list
y = data_list.part_1()
details_file_path = pdf_file_path.replace(".pdf", "_summary.csv")
data_list.to_csv(y, details_file_path)

        # Process part 2 (det)
#data_list = Verizon(pdf_file_path)
x = data_list2.part_2()
summary_file_path = pdf_file_path.replace(".pdf", "_details.csv")
data_list.to_csv(x, summary_file_path)

