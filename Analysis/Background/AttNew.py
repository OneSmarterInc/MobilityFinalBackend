import pandas as pd
import pdfplumber,re,time


class AttClass:
    def __init__(self,path):
        self.path = path
        self.account_number = None
        self.invoice_number = None
        self.bill_date = None
        self.due_date = None
        self.bill_period = None
        self.key = None
        self.url = "http://www.business.att.com/"
        self.billing = {}
        self.remmitance = "PO Box 6463 Carol Stream, IL 60197-6463"
        self.duration = None
        self.unique_key_pattern = re.compile(r'(?:\d{3}[-.]){2}\d{4}\s+[A-Za-z]+\s+[A-Za-z]+\s+\d+\s+(?:\$\d+(?:\.\d{2})?|-)', re.IGNORECASE)
        self.details_key_pattern = re.compile(r"^[A-Z][a-z]+\s*,\s*\(?\d{3}\)?[.\s-]?\d{3}[.\s-]?\d{4}", re.IGNORECASE)
        self.planSide = None


    def initial_page_data(self,pages):
        print("def initial_page_data")
        page = pages[0]
        
        width = page.width
        height = page.height
        self.x0 = width/2
        top_half_bbox = (0, 0, width, height / 4)
        bottom_half_bbox = (0, height / 1.5, width, height)
        top_half = page.within_bbox(top_half_bbox)
        bottom_half = page.within_bbox(bottom_half_bbox)
        words = bottom_half.extract_words(extra_attrs=["size", "fontname"])
        for i in range(len(words) - 1):
            if "pay" in words[i]['text'].lower():
                self.x0 = words[i]['x0']
                break
        top_text = top_half.extract_text()
        bottom_text = bottom_half.extract_text()
        account_number_match = re.search(r"Account Number: ([\d\-]+)", top_text)
        self.account_number = account_number_match.group(1) if account_number_match else None

        invoice_number_match = re.search(r"Invoice:\s*(\S+)", top_text)
        self.invoice_number = invoice_number_match.group(1) if invoice_number_match else None

        bill_date_match = re.search(r"Issue Date:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", top_text)
        self.bill_date = bill_date_match.group(1).replace(",","") if bill_date_match else None

        amount_match = re.search(r"\$[\d,]+\.\d{2}", bottom_text)
        self.total_amount = amount_match.group() if amount_match else None
        due_date_match = re.search(r"([A-Za-z]+\s+\d{1,2},\s+\d{4})", bottom_text)
        self.due_date = due_date_match.group(1).replace(",","") if due_date_match else None

        bottom_left_box = (0, height / 1.5, self.x0-10, height-100)
        bottom_right_box = (width/2, height / 1.5, width, height-50)
        bottom_left = page.within_bbox(bottom_left_box)
        bottom_right = page.within_bbox(bottom_right_box)

        bottom_left_text = bottom_left.extract_text()
        bottom_left_text = re.sub(r"(\d{5}-\d{4}).*$", r"\1", bottom_left_text, flags=re.DOTALL)
        bottom_right_text = bottom_right.extract_text()

        pattern = re.compile(
            r"PO Box\s+\d+\s*\n[A-Za-z ]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?",
            re.MULTILINE
        )
        lines = bottom_left_text.split("\n")
        for i,line in enumerate(lines):
            if "attn" in line.lower():
                self.billing["attn"] = line.split(":")[-1].strip()
                self.billing["name"] = lines[i-1].strip()
                self.billing["address"] = " ".join(lines[i+1:i+4]).strip()
        if not self.billing:
            self.billing["address"] = f'{lines[-2]} {lines[-1]}'.strip()
            self.billing["name"] = lines[-3].strip()
                
        match = pattern.search(bottom_right_text)
        self.remmitance = match.group(0).replace("\n"," ") if match else self.remmitance

        
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

    def clean_and_sum(self, lst):
        return sum(
            map(lambda x: 0 if x.strip() == '-' else float(x.replace('$', '')),
                lst)
        )
        
    def unique_data(self,pages):
        print("def unique_data")
        all_lines = []
        lines_data = []
        group_data = []
        groups = {}
        self.group = None
        pattern = r'^(?:\d{3}[-.]){2}\d{4}.*(?:--|\$\d+(?:\.\d{2})?)'
        for page in pages:
            data = page.extract_text()
            lines = data.splitlines()
            filtered_lines = []
            for line in lines:
                items = line.split(" ")
                if "group" in line.lower():
                    # if re.search(g_match, line.strip()):
                    if line.lower().startswith("group"):
                        self.group = " ".join(items[0:2])
                        groups[self.group] = {"numbers":[], "amount":"0"}
                        groups[self.group]["amount"] = items[-1] if "$" in items[-1] else "0"
                    if "total" in line.lower():
                        self.group = None
                if line.strip().lower().startswith("total"):
                    break 
                if self.group and re.search(pattern, line.strip()):
                    groups[self.group]["numbers"].append(line.split(" ")[0])
                filtered_lines.append(line)
            matching_lines = [line for line in filtered_lines if re.search(pattern, line.strip())]
            all_lines += matching_lines
        for line in all_lines:
            line = line.split()
            activity_pattern = re.compile(r"^-$|^-?\$?\d+\.\d{2}$")
            activity_index = next((i for i, v in enumerate(line) if activity_pattern.match(v)), None)
            page_index = activity_index - 1
            monthly_charges = self.clean_and_sum(line[activity_index+1:-3])
            monthly_charges = f'-${monthly_charges:.2f}' if monthly_charges < 0 else f'${monthly_charges:.2f}'
            lines_data.append({
                "Wireless Number": line[0],
                "Username" : " ".join(line[1: page_index]),
                "Page": line[page_index],
                "Activity since last bill": line[activity_index],
                "Monthly Charges": monthly_charges,
                "Company fees and surcharges": line[-3],
                "Government fees and taxes": line[-2],
                "Total Charges": line[-1],
            })

        for key,value in groups.items():
            numbers = value.get("numbers")
            amount = value.get("amount").replace("$","").replace(",","")
            each_get = float(amount) / len(numbers)
            for num in numbers:
                group_data.append({
                    "Wireless Number":num,
                    "Group":key,
                    "Group Charges":each_get
                })
        
        unique = pd.DataFrame(lines_data)
        group_df = pd.DataFrame(group_data)
        if not group_df.empty:
            unique['Total Charges'] = (
                unique['Total Charges']
                .astype(str)
                .str.replace(r'[$,]', '', regex=True)
                .replace('', '0')
                .astype(float)
            )

            group_df['Group Charges'] = (
                group_df['Group Charges']
                .astype(str)
                .str.replace(r'[$,]', '', regex=True)
                .replace('', '0')
                .astype(float)
            )

            unique = pd.merge(unique, group_df, on="Wireless Number", how="left")

            unique['Total Charges'] = (
                unique['Total Charges'].fillna(0) + unique['Group Charges'].fillna(0)
            ).apply(lambda x: f"${x:,.2f}")
            unique = unique.fillna("NA")
            unique = unique.drop(columns=["Group Charges"])
        charges_list = list(unique["Total Charges"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(float))
        sum_of_total_charges = sum(charges_list)
        print(round(sum_of_total_charges,2))
        unique = unique.replace(r'^\s*-\s*$', 'NA', regex=True)
        return unique
    
    def separate_words(self, text):
        words = re.findall(r'[A-Z][a-z]*|[a-z]+|[A-Z]+(?![a-z])', text)
        for word in words:
            if "Charges" in word and len(word) > len("Charges"):
                separate = list(str(word).strip().partition("Charges"))
                newWord = " ".join(separate).strip()
                words[words.index(word)] = newWord
        return " ".join(words)
        
    
    def plan_data(self,pages,unique_df):
        category_dict = {}
        final_data = []
        all_charges_data = {}
        all_plan_data = {}
        final_plan_data = []
        print("def baseline_data")
        wn_pattern = r"\d{3}[-.]\d{3}[-.]\d{4}"
        page = pages[0]
        self.x0 = page.width / 2
        self.maxHeight = page.height
        words = page.extract_words(extra_attrs=["size", "fontname"])
        for i in range(len(words) - 1):
            if "usage" in words[i]['text'].lower() and "summary" in words[i+1]['text'].lower():
                self.x0 = words[i]['x0']
                break
            if "continue" in words[i]['text'].lower():
                self.maxHeight = words[i]['top'] + 1
        if self.x0 < page.width/2:
            self.planSide = "left"
        elif self.x0 > page.width/2:
            self.planSide = "right"

        if self.planSide == "left":
            planBox = (0, self.maxHeight, self.x0+170, page.height-20)
            chargesBox = (self.x0+175, self.maxHeight, page.width, page.height-50)
        elif self.planSide == "right":
            planBox = (self.x0-10, self.maxHeight, page.width, page.height-20)
            chargesBox = (0, self.maxHeight, self.x0-10, page.height-50)

        self.wn = None
        
        for page in pages:
            charges = page.within_bbox(chargesBox)
            
            words = charges.extract_words(extra_attrs=["size", "fontname"])
            for word in words:
                top = round(float(word['top']), 2)
                if word['fontname'] == "EAAAAA+ATTAleckSans-Medium":
                    if not top in category_dict.keys():
                        category_dict[top] = ""
                    category_dict[top] += " " + word['text'] if not word['text'] in category_dict[top] else ""

            
            charges_text = charges.extract_text()
            lines = charges_text.splitlines()
            self.key = None
            for line in lines:
                wn_match = re.findall(wn_pattern,line)
                if not 'total' in line.lower() and wn_match:
                    self.wn = wn_match[0]
                    all_charges_data[self.wn] = ""
                    self.category = None
                if self.wn:
                    all_charges_data[self.wn] += "\n" + line 
                if 'total' in line.lower() and wn_match:
                    self.wn = None

            words = page.extract_words()
            plans = page.within_bbox((0, self.maxHeight, page.width, page.height-50))
            plans_text = plans.extract_text()
            lines = plans_text.splitlines()
            
            for line in lines:
                wn_match = re.findall(wn_pattern,line)
                if "usage summary" in line.lower():
                    self.key = "start"
                if not 'total' in line.lower() and wn_match:
                    self.wn = wn_match[0]
                    all_plan_data[self.wn] = ""
                if self.wn and self.key:
                    all_plan_data[self.wn] += "\n" + line if (line.lower().endswith("used") or (
                        re.search(r"\d{1,3}(?:,\d{3})*(?:\.\d+)?$", line) 
                            and not re.search(r"\$\d{1,3}(?:,\d{3})*(?:\.\d+)?$", line.strip())  
                            )
                        ) else ""
                    
                if 'total' in line.lower() and wn_match:
                    self.wn = None
                    self.key = None

        wn_pattern = re.compile(wn_pattern)
        category_lst = list(set([
            cat.strip()
            for cat in category_dict.values()
            if not wn_pattern.search(cat)
        ]))
        pattern1 = r"^[\u2022\-]?\s*(.+?)\s+(-?\$\d+\.\d{2})$"
        pattern2 =r"(.+?)\s+(-?\$?(?:\d+\.\d{2}|\.\d{2}))"
        self.category = None
        for wn, chargesText in all_charges_data.items():
            lines = [line for line in chargesText.splitlines() if "total" not in line.lower()]
            lines = [line for line in lines if "usage" not in line.lower()]
            for line in lines:
                line = re.sub(
                    r"(?i)\s*[-,]?\s*(?:\d{2}/\d{2}\s*-\s*\d{2}/\d{2}|[A-Za-z]{3,9}\s+\d{1,2})\s*[-,]?\s*",
                    " ",
                    line
                ).strip()
                if line in category_lst:
                    matches = re.findall(pattern2, line)
                    if matches:
                        for cat, amount in matches:
                            self.category = self.separate_words(cat.strip())                                  
                    else:
                        self.category = self.separate_words(line.strip())
                else:
                    matches = re.findall(pattern1, line)
                    if matches:
                        final_data.append({
                            "Wireless Number": wn,
                            "Item Category": self.category,
                            "Item Description":" ".join(matches[0][0].strip().split()[1:]),
                            "Charges":matches[0][1].strip()
                        })
        for wn, planText in all_plan_data.items():
            lines = planText.splitlines()
            wnplan = ""
            self.head = None
            patt = r"\$\d{1,3}(?:,\d{3})*(?:\.\d+)?"
            for i,line in enumerate(lines):
                match = re.search(patt, line)
                line = line[match.start():].strip() if match and not line.strip().endswith(match.group()) else line
                if line.lower().endswith("used"):
                    self.head = " ".join(line.split(" ")[-2:]) 
                if self.head and self.head not in line:

                    wnplan += f'{self.head} {line}, '
            # print(wnplan.replace("Used",":"))
            plan_str = wnplan.split(",")[-2] if len(wnplan.split(","))>1 else wnplan.split(",")[-1]
            if "data" in plan_str.lower():
                data_usage = plan_str.split(" ")[-1]
            else:
                data_usage = "NA"
            final_plan_data.append({"Wireless Number":wn, "Plan":plan_str if "data" in plan_str.lower() else "", "Data Usage":data_usage})

        df = pd.DataFrame(final_data)
        if unique_df is not None:
            baseline_df = pd.merge(unique_df, df, on="Wireless Number")  
        else:
            baseline_df = df
        planDf = pd.DataFrame(final_plan_data)
        if not planDf.empty:
            planDf["Plan"] = planDf["Plan"].apply(lambda x: x.strip())
            planDf["Plan"] = planDf["Plan"].apply(lambda x: x.replace("  ", " "))
            baseline_df = pd.merge(baseline_df, planDf, on="Wireless Number") 

        # group baseline_df by Wireless Number and get first Item Description and replace it with Plan in Unique_df
        if "Item Description" in baseline_df.columns and "Plan" in baseline_df.columns:
            desc_map = baseline_df.groupby("Wireless Number")["Item Description"].first().to_dict()
            baseline_df["Plan"] = baseline_df["Wireless Number"].map(desc_map).fillna(baseline_df["Plan"])
            baseline_df = baseline_df.drop(columns=["Item Description"])

        return baseline_df
    
    def format_wn(self, df):
        df["Wireless Number"] = (
            df["Wireless Number"]
            .astype(str)
            .str.replace(r"\D", "", regex=True)
            .str.replace(r"(\d{3})(\d{3})(\d{4})", r"\1-\2-\3", regex=True)
        )
        return df
    
    def extract_all(self):
        
        start_time = time.perf_counter()
        total_pattern = re.compile(r"Total\s+for\s+(?:\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})\s+-?\$\d+\.\d{2}",re.IGNORECASE)
        matching_page_basic = []
        matching_pages_unique = []
        matching_pages_baseline = []
        matching_plan_pages = []
        with pdfplumber.open(self.path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if (("account" and "invoice") in text.lower()):
                    if not matching_page_basic:
                        matching_page_basic.append(page)
                if text and self.unique_key_pattern.search(text):
                    matching_pages_unique.append(page)
                if text and "usage is rounded up based on your plan" in text.lower():
                    matching_plan_pages.append(page)
                if text and (self.details_key_pattern.search(text) or total_pattern.search(text)):
                    # if matching_pages_baseline:
                    #     break
                    matching_pages_baseline.append(page)
                if "news you can use" in text.lower():
                    break
        print("plan_pages==", matching_plan_pages)
        basic = self.initial_page_data(matching_page_basic)
        unique_df = self.unique_data(matching_pages_unique)
        charges_list = list(unique_df["Total Charges"].str.replace("$", "", regex=False).str.replace(",", "", regex=False).astype(float))
        sum_of_total_charges = sum(charges_list)
        basic["Total Charges"] = f'${round(sum_of_total_charges,2)}'
        baseline_df = self.plan_data(matching_pages_baseline,unique_df)
        plan_df = baseline_df[["Wireless Number", "Plan", "Data Usage"]]
        plan_df = plan_df.drop_duplicates(subset=["Wireless Number", "Plan"])
        unique_df = unique_df.merge(plan_df, on="Wireless Number", how="left")
        
        # reorder unique df to put Plan just before Monthly Charges
        if "Plan" in unique_df.columns:
            cols = list(unique_df.columns)
            plan_index = cols.index("Plan")
            monthly_index = cols.index("Monthly Charges")
            if plan_index > monthly_index:
                cols.insert(monthly_index, cols.pop(plan_index))
            unique_df = unique_df[cols]
        else:
            unique_df.insert(unique_df.columns.get_loc("Monthly Charges"), "Plan", "")
        


        process_finish_time = time.perf_counter()
        tt = process_finish_time - start_time
        return basic, self.format_wn(unique_df), round(float(tt), 2)
    

# obj = AttClass("Bills/media/BanUploadBill/ATT_Mobility_MPP.pdf")
# basic, plandf,t = obj.extract_all()
# print(basic)
# print(plandf)
# plandf.to_csv("plandf.csv", index=False)

