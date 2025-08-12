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
        self.duration = None
        self.url = "http://sso.verizonenterprise.com"
        self.billing = {}
        self.planSide = None
        self.unique_key_pattern = re.compile(r'(?:\d{3}[-.]){2}\d{4}\s+[A-Za-z]+\s+[A-Za-z]+\s+\d+\s+(?:\$\d+(?:\.\d{2})?|--)', re.IGNORECASE)
        self.details_key_pattern = re.compile(r"(?=.*\bTotal\b)(?=.*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", re.IGNORECASE)

        self.company_name = "SimpleTek"
        self.sub_company = "BABW"
        self.vendor = "Verizon"
        self.month = "July"
        self.year = 2024
    
    def initial_page_data(self,pages):
        page = pages[0]

        width = page.width
        height = page.height
        top_half_bbox = (0, 0, width, height / 2)
        top_half = page.within_bbox(top_half_bbox)
        top_text = top_half.extract_text()
        duration_match = re.findall(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*-\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\b', top_text)
        if duration_match:
            self.duration = duration_match[0]
        url_match = re.findall(r'\b(?:https?://|www\.)[^\s/$.?#].[^\s]*',top_text)
        if url_match:
            self.url = url_match[0]
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
            "Remittance Info": self.remmitance,
            "Duration": self.duration,
            "Vendor Url": self.url
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
    def separate_words(self, text):
        words = re.findall(r'[A-Z][a-z]*|[a-z]+|[A-Z]+(?![a-z])', text)
        for word in words:
            if "Charges" in word and len(word) > len("Charges"):
                separate = list(str(word).strip().partition("Charges"))
                newWord = " ".join(separate).strip()
                words[words.index(word)] = newWord
        return " ".join(words)
    def baseline_data(self,pages,unique_df=None):
        final_data = []
        final_plan_data = []
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
        
        if self.planSide == "left":
            planBox = (0, 0, self.x0+170, page.height-20)
            chargesBox = (self.x0+175, 0, page.width, page.height)
        elif self.planSide == "right":
            planBox = (self.x0-10, 0, page.width, page.height-20)
            chargesBox = (0, 0, self.x0-10, page.height)
        pattern =r"(.+?)\s+(-?\$?(?:\d+\.\d{2}|\.\d{2}))"
        
        for page in pages:
            
            plan = page.within_bbox(planBox)
            plan_text = plan.extract_text()
            match = re.search(r"(?:Your)?Plan\s*(.*)", plan_text, re.DOTALL | re.MULTILINE | re.IGNORECASE)
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
                            self.category = self.separate_words(cat.strip())                                  
                    else:
                        self.category = self.separate_words(line.strip())
                else:
                    matches = re.findall(pattern, line)
                    if matches:
                        final_data.append({
                            "Wireless Number": wn,
                            "Item Category": self.category,
                            "Item Description":matches[0][0].strip(),
                            "Charges":matches[0][1].strip()
                        })
        for wn, planText in all_plan_data.items():
            # print(planText)
            lines = planText.splitlines()
            Separatorline= [line for line in lines if line.strip() and "charges?" in line.lower()]
            lines = lines[:lines.index(Separatorline[0])] if Separatorline else lines
            plan = " ".join(lines).strip()
            final_plan_data.append({
                "Wireless Number": wn,
                "Plans": plan
            })
        df = pd.DataFrame(final_data)
        if unique_df is not None:
            baseline_df = pd.merge(unique_df, df, on="Wireless Number")  
        else:
            baseline_df = df
        planDf = pd.DataFrame(final_plan_data)
        if not planDf.empty:
            planDf["Plans"] = planDf["Plans"].apply(lambda x: x.strip())
            planDf["Plans"] = planDf["Plans"].apply(lambda x: x.replace("  ", " "))
            baseline_df = pd.merge(baseline_df, planDf, on="Wireless Number") 

        if "Plans" in baseline_df.columns:
                cols = list(baseline_df.columns)
                plan_index = cols.index("Plans")
                monthly_index = cols.index("Monthly Charges")
                if plan_index > monthly_index:
                    cols.insert(monthly_index, cols.pop(plan_index))
                baseline_df = baseline_df[cols]
        else:
            baseline_df.insert(baseline_df.columns.get_loc("Monthly Charges"), "Plans", "")
        return baseline_df

    def extract_all(self):
        matching_page_basic = []
        matching_pages_unique = []
        matching_pages_baseline = []
        with pdfplumber.open(self.path) as pdf:
            extraction_start_time = time.perf_counter()
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if (("account" and "invoice" and "keyline") in text.lower()):
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

            process_start_time = time.perf_counter()
            basic_data = self.initial_page_data(matching_page_basic)
            unique_df = self.unique_data(matching_pages_unique)
            baseline_df = self.baseline_data(matching_pages_baseline, unique_df=unique_df)

            plan_df = baseline_df[["Wireless Number", "Plans"]]
            plan_df = plan_df.drop_duplicates(subset=["Wireless Number", "Plans"])
            unique_df = unique_df.merge(plan_df, on="Wireless Number", how="left")
            # reorder unique df to put Plan just before Monthly Charges
            if "Plans" in unique_df.columns:
                cols = list(unique_df.columns)
                plan_index = cols.index("Plans")
                monthly_index = cols.index("Monthly Charges")
                if plan_index > monthly_index:
                    cols.insert(monthly_index, cols.pop(plan_index))
                unique_df = unique_df[cols]
            else:
                unique_df.insert(unique_df.columns.get_loc("Monthly Charges"), "Plans", "")

            
            process_finish_time = time.perf_counter()
            process_time = process_finish_time - process_start_time
            print(f"{(extraction_time + process_time):.2f}", "seconds to process the PDF")
            return basic_data, unique_df, baseline_df, round(float(extraction_time + process_time), 2)

# obj = VerizonClass("Bills/media/ViewUploadedBills/Verizon.pdf")
# basic, unique, baseline,t = obj.extract_all()

# print(unique[["Wireless Number", "Plans"]].head(10))
# unique.to_csv("unique.csv", index=False)
# baseline.to_csv("baseline.csv", index=False)