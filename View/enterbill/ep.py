import pandas as pd
import json
import time
from OnBoard.Ban.models import PdfDataTable, UniquePdfDataTable, BaseDataTable, BaselineDataTable
import re
import numpy as np
import json

class EnterBillProcessExcel:
    def __init__(self, buffer_data,instance,typeofupload=None):

        print("init")
        self.instance = instance
        self.buffer_data = json.loads(buffer_data) if isinstance(buffer_data, str) else buffer_data
        print(type(self.buffer_data))
        self.type = typeofupload
        self.company = self.buffer_data.get('company')
        self.vendor = self.buffer_data.get('vendor')
        self.account_number = self.buffer_data.get('account_number')
        self.sub_company = self.buffer_data.get('sub_company')
        self.mapping_data = self.buffer_data.get('mapping_json')
        self.excel_csv_path = self.buffer_data.get('excel_csv_path')
        self.entry_type = self.buffer_data.get('entry_type')
        self.master_account = self.buffer_data.get('master_account')
        self.location = self.buffer_data.get('location')
        self.month = self.buffer_data.get('month')
        self.year = self.buffer_data.get('year')

        print("init complete")

    def format_wireless_number(self, number):
        pattern2 = r'^\d{3}\-\d{3}\-\d{4}$'
        if len(str(number)) <= 10:
            return
        if re.match(pattern2, str(number)):
            return number
        pattern = r'^\d{3}\.\d{3}\.\d{4}$'
        
        if re.match(pattern, str(number)):
            return str(number).replace('.','-')
        
        cleaned_number = str(number).replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
        cleaned_number = '-'.join(cleaned_number.split('-'))
        formatted_number = cleaned_number[:3] + "-" + cleaned_number[3:6] + "-" + cleaned_number[6:]
        return formatted_number
    
    def process_excel(self):
        print("process excel")
        df_csv = pd.read_excel(self.excel_csv_path)
        print("length of csv",len(df_csv))
        df_csv.columns = df_csv.columns.str.strip()
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

        latest_entry_dict = self.mapping_data.copy()

        for key, value in latest_entry_dict.items():
            latest_entry_dict[key] = str(value).replace(' ', '_')
            
        column_mapping = {v: k for k, v in latest_entry_dict.items()}
        filtered_mapping = {key: value for key, value in column_mapping.items() if key != 'NA'}

        for key, value in latest_entry_dict.items():
            if value == "NA":
                latest_entry_dict[key] = key
        
        columns_to_keep = [col for col in latest_entry_dict.values() if col in df_csv.columns]
        df_csv = df_csv[columns_to_keep]
        df_csv.rename(columns=filtered_mapping, inplace=True)
        df_csv.replace('', np.nan, inplace=True)

        # Drop rows with any NaN (i.e., blank cells)
        df_csv.dropna(how='all', inplace=True)
        print("new df csv====",len(df_csv))
        print(df_csv)
        rw = df_csv.iloc[0]
        base_dict = rw.to_dict()

        print(base_dict)
        file_vendor = base_dict.get('vendor')
        file_account_number = base_dict.get('account_number')
        file_bill_date = base_dict.get('bill_date')

        if file_vendor != self.vendor:
            return {"message":f"Input vendor {self.vendor} not matched with excel vendor {file_vendor}!", 'code':1}

        print("vendor checked")
        print(file_account_number, self.account_number)
        if str(file_account_number) != str(self.account_number):
            return {"message":f"Input account number {self.account_number} not matched with excel account number {file_account_number}!", 'code':1}

        print("account number checked")
        check_ban = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(accountnumber=file_account_number)
        if not check_ban.exists():
            return {"message":f"Account number {file_account_number} not found!", 'code':1}
        
        print("account number presence checked")
        
        bill_date = file_bill_date.replace(",","").split(" ")
        print(bill_date)
        file_bill_date = " ".join(bill_date)

        if not (bill_date[0] in str(self.month)):
            return {'message' : f'Bill date from the excel file did not matched with input month', 'code' : 1}
        print("month checked")
        if self.year != bill_date[2]:
            return {'message' : f'Bill date from the excel file did not matched with input year', 'code' : 1}
        print("year checked")
        if BaseDataTable.objects.filter(accountnumber=file_account_number, company=self.company, sub_company=self.sub_company, month=self.month, year=self.year).exists():
            return {'message' : f'Bill already exists for account number {file_account_number}', 'code' : 1}
        
        print("existance checked")
        base_dict['company'] = self.company
        base_dict['vendor'] = self.vendor
        base_dict['sub_company'] = self.sub_company
        base_dict['accountnumber'] = base_dict['account_number']
        base_dict['Entry_type'] = self.entry_type
        base_dict['location'] = self.location
        base_dict['master_account'] = self.master_account
        base_dict['bill_date'] = file_bill_date
        
        keys_to_keep = ['company', 'vendor', 'sub_company', 'accountnumber', 'Entry_type', 'location', 'master_account','bill_date']
        b_dict = {key: base_dict[key] for key in keys_to_keep if key in base_dict}
        

        onboarded = BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).filter(sub_company=self.sub_company, vendor=self.vendor, accountnumber=self.account_number).first()
        # Insert into BaseDataTable
        BaseDataTable.objects.create(viewuploaded=self.instance,month=self.month, year=self.year,RemittanceAdd=onboarded.RemittanceAdd, **b_dict)
        print("Data added to BaseDataTable")
        
        df_csv['wireless_number'] = df_csv['wireless_number'].apply(self.format_wireless_number)
        df_csv_dict = df_csv.to_dict(orient='records')
        
        for item in df_csv_dict:
            item['company'] = self.company
            item['bill_date'] = file_bill_date
            item['vendor'] = self.vendor
            item['sub_company'] = self.sub_company
            item['account_number'] = self.account_number
            item['entry_type'] = self.entry_type
        # Bulk insert into UniquePDFDataTable
        UniquePdfDataTable.objects.bulk_create([UniquePdfDataTable(**item,viewuploaded=self.instance) for item in df_csv_dict])
        print("Data added to UniquePdfDataTable")

        df_csv = pd.DataFrame(df_csv_dict)
        df_csv = df_csv.rename(columns={'wireless_number': 'Wireless_number'})

        df_csv_dict = df_csv.to_dict(orient='records')

        model_fields = [field.name for field in BaselineDataTable._meta.get_fields() if field.concrete and not field.auto_created]

        # Prepare clean items
        clean_items = [
            BaselineDataTable(viewuploaded=self.instance, **{k: v for k, v in item.items() if k in model_fields})
            for item in df_csv_dict
        ]

        BaselineDataTable.objects.bulk_create(clean_items)
        return {"message":"Bill uploaded successully", 'code':0}

    
class EnterBillProcessExcel1:
    def __init__(self, buffer_data,instance,typeofupload=None):

        print("init")
        self.instance = instance
        self.buffer_data = json.loads(buffer_data) if isinstance(buffer_data, str) else buffer_data
        print(type(self.buffer_data))
        self.type = typeofupload
        self.company = self.buffer_data.get('company')
        self.csv_path = self.buffer_data.get('csv_path')
        self.vendor = self.buffer_data.get('vendor')
        self.account_number = self.buffer_data.get('account_number')
        self.sub_company = self.buffer_data.get('sub_company')
        self.mapping_data = self.buffer_data.get('mapping_json')
        self.location_csv_path = self.buffer_data.get('location_csv_path')
        self.excel_csv_path = self.buffer_data.get('excel_csv_path')
        self.entry_type = self.buffer_data.get('entry_type')
        self.master_account = self.buffer_data.get('master_account')
        self.location = self.buffer_data.get('location')
        self.month = self.buffer_data.get('month')
        self.year = self.buffer_data.get('year')

        print("init complete")

    def process_csv_from_buffer(self):
        print("process csv from buffer")
        if self.csv_path:
            print("csv_path: " + self.csv_path)
            self.process_csv_data()
        elif self.location_csv_path:
            loc_csv_path = self.location_csv_path
            self.process_location_csv_data(loc_csv_path)
        elif self.excel_csv_path:
            ex_path = self.excel_csv_path
            msgobj = self.process_excel_csv_data(ex_path)
            return msgobj
    
    def process_excel_csv_data(self, csv_path):
        print("process excel csv data")
        df_csv = pd.read_excel(csv_path)

        print("length of csv",len(df_csv))
        print(df_csv)
        df_csv.columns = df_csv.columns.str.strip()
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')


        print("columns of csv", df_csv.columns)
        def format_wireless_number(number):
            pattern2 = r'^\d{3}\-\d{3}\-\d{4}$'
            if len(str(number)) <= 10:
                return
            if re.match(pattern2, str(number)):
                return number
            pattern = r'^\d{3}\.\d{3}\.\d{4}$'
            
            if re.match(pattern, str(number)):
                return str(number).replace('.','-')
            
            cleaned_number = str(number).replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
            cleaned_number = '-'.join(cleaned_number.split('-'))
            formatted_number = cleaned_number[:3] + "-" + cleaned_number[3:6] + "-" + cleaned_number[6:]
            return formatted_number
    
        def process_data(df_csv):
            latest_entry_dict = self.mapping_data.copy()
            for key, value in latest_entry_dict.items():
                latest_entry_dict[key] = str(value).replace(' ', '_')
            
            column_mapping = {v: k for k, v in latest_entry_dict.items()}
            filtered_mapping = {key: value for key, value in column_mapping.items() if key != 'NA'}

            for key, value in latest_entry_dict.items():
                if value == "NA":
                    latest_entry_dict[key] = key
            
            columns_to_keep = [col for col in latest_entry_dict.values() if col in df_csv.columns]
            df_csv = df_csv[columns_to_keep]
            df_csv.rename(columns=filtered_mapping, inplace=True)
            df_csv.replace('', np.nan, inplace=True)

            # Drop rows with any NaN (i.e., blank cells)
            df_csv.dropna(how='all', inplace=True)
            print("new df csv====",len(df_csv))
            print(df_csv)
            rw = df_csv.iloc[0]
            base_dict = rw.to_dict()

            print(base_dict)
            file_vendor = base_dict.get('vendor')
            file_account_number = base_dict.get('account_number')
            file_bill_date = base_dict.get('bill_date')

            if file_vendor != self.vendor:
                return {"message":f"Input vendor {self.vendor} not matched with excel vendor {file_vendor}!", 'code':1}

            print("vendor checked")
            print(file_account_number, self.account_number)
            if file_account_number != self.account_number:
                return {"message":f"Input account number {self.account_number} not matched with excel account number {file_account_number}!", 'code':1}

            print("account number checked")
            check_ban = BaseDataTable.objects.filter(viewuploaded=None, viewpapered=None).filter(accountnumber=file_account_number)
            if not check_ban.exists():
                return {"message":f"Account number {file_account_number} not found!", 'code':1}
            
            print("account number presence checked")

            bill_date = file_bill_date.replace(",","").split(" ")
            file_bill_date = " ".join(bill_date)

            print(file_bill_date)
            if not (file_bill_date[0] in str(self.month)):
                return {'message' : f'Bill date from the excel file did not matched with input month', 'code' : 1}
            print("month checked")
            if self.year != file_bill_date[2]:
                return {'message' : f'Bill date from the excel file did not matched with input year', 'code' : 1}
            print("year checked")
            if BaseDataTable.objects.filter(accountnumber=file_account_number, company=self.company, sub_company=self.sub_company, month=self.month, year=self.year).exists():
                return {'message' : f'Bill already exists for account number {file_account_number}', 'code' : 1}
            
            print("existance checked")
            base_dict['company'] = self.company
            base_dict['vendor'] = self.vendor
            base_dict['sub_company'] = self.sub_company
            base_dict['accountnumber'] = base_dict['account_number']
            base_dict['Entry_type'] = self.entry_type
            base_dict['location'] = self.location
            base_dict['master_account'] = self.master_account
            base_dict['bill_date'] = file_bill_date
            
            keys_to_keep = ['company', 'vendor', 'sub_company', 'accountnumber', 'Entry_type', 'location', 'master_account','bill_date']
            b_dict = {key: base_dict[key] for key in keys_to_keep if key in base_dict}
            

            onboarded = BaseDataTable.objects.filter(viewuploaded=None,viewpapered=None).filter(sub_company=self.sub_company, vendor=self.vendor, accountnumber=self.account_number).first()
            # Insert into BaseDataTable
            BaseDataTable.objects.create(viewuploaded=self.instance,month=self.month, year=self.year,RemittanceAdd=onboarded.RemittanceAdd, **b_dict)
            print("Data added to BaseDataTable")
            
            df_csv['wireless_number'] = df_csv['wireless_number'].apply(format_wireless_number)
            df_csv_dict = df_csv.to_dict(orient='records')
            
            for item in df_csv_dict:
                item['company'] = self.company
                item['bill_date'] = file_bill_date
                item['vendor'] = self.vendor
                item['sub_company'] = self.sub_company
                item['account_number'] = self.account_number
                item['entry_type'] = self.entry_type
            # Bulk insert into UniquePDFDataTable
            UniquePdfDataTable.objects.bulk_create([UniquePdfDataTable(**item,viewuploaded=self.instance) for item in df_csv_dict])
            print("Data added to UniquePdfDataTable")

            df_csv = pd.DataFrame(df_csv_dict)
            df_csv = df_csv.rename(columns={'wireless_number': 'Wireless_number'})

            df_csv_dict = df_csv.to_dict(orient='records')

            model_fields = [field.name for field in BaselineDataTable._meta.get_fields() if field.concrete and not field.auto_created]

            # Prepare clean items
            clean_items = [
                BaselineDataTable(viewuploaded=self.instance, **{k: v for k, v in item.items() if k in model_fields})
                for item in df_csv_dict
            ]

            BaselineDataTable.objects.bulk_create(clean_items)
            print("Data added to BaselineTable")
        
        process_data(df_csv)
    def process_location_csv_data(self, csv_path):
        print("process_location_csv_data")
        # Load the Excel file into a pandas DataFrame
        df_csv = pd.read_excel(csv_path)
        
        # Clean up the column names in the CSV
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

        # Connect to the database
        import time

        from OnBoard.Location.models import Location as AddLocation

        def fetch_latest_entry():
            return AddLocation.objects.order_by('-id').first()

        def is_location_done(entry_dict):
            return entry_dict.get('location_type') == 'Done'

        while True:
            # Fetch the latest mapping entry
            latest_entry = fetch_latest_entry()

            # Check if no entry is returnedF
            if latest_entry is None:
                print("No entry found in the 'myapp_location_mappingdata' table.")
                break  # Exit the function if no entry is found

            # Convert model instance to dictionary
            latest_entry_dict = {field.name: getattr(latest_entry, field.name) for field in AddLocation._meta.fields}
            
            # Remove 'id' from the mapping
            latest_entry_dict.pop('id', None)
            
            # Clean up column mapping dictionary
            for key, value in latest_entry_dict.items():
                if isinstance(value, str):
                    latest_entry_dict[key] = value.replace(' ', '_')

            # If location_type is 'Done', wait for 2 seconds and skip further processing
            if is_location_done(latest_entry_dict):
                time.sleep(2)
            else:
                # Create column mappings (mapping CSV columns to DB columns)
                column_mapping = {v: k for k, v in latest_entry_dict.items() if v is not None}
                filtered_mapping = {key: value for key, value in column_mapping.items() if key != 'NA'}

                # Replace 'NA' columns with their respective keys
                for key, value in latest_entry_dict.items():
                    if value == "NA":
                        latest_entry_dict[key] = key

                # Filter the DataFrame to keep only columns that exist in both the CSV and DB
                columns_to_keep = [col for col in latest_entry_dict.values() if col in df_csv.columns]
                df_csv = df_csv[columns_to_keep]

                # Rename columns in the DataFrame based on the column mappings
                df_csv.rename(columns=filtered_mapping, inplace=True)

                # Mark the location type as 'Done' in the mapping
                latest_entry.location_type = 'Done'
                latest_entry.save()

                # Break the loop once mapping is done
                break

        # Insert the mapped CSV data into the AddLocation table
        df_dict = df_csv.to_dict(orient='records')

        # Get company_name and sub_company_name from the mapping object
        company_name = latest_entry_dict.get('company_name')
        sub_company_name = latest_entry_dict.get('sub_company_name')

        for item in df_dict:
            # Add company_name and sub_company_name to each row
            item['company_name'] = company_name
            item['sub_company_name'] = sub_company_name

            # Insert into AddLocation model
            AddLocation.objects.create(**item)
            print("Data added to AddLocation")
    def process_csv_data(self):
        print("Process CSV data")
        df_csv = pd.read_excel(self.csv_path)
        df_csv.columns = df_csv.columns.str.strip()
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

        
        latest_entry_dict =  json.loads(json.dumps(self.mapping_data))
        
        # print(latest_entry_dict, type(latest_entry_dict))
        # latest_entry_dict = str(latest_entry_dict)
        # print(latest_entry_dict, type(latest_entry_dict))
        # latest_entry_dict = json.loads(latest_entry_dict)
        for key, value in latest_entry_dict.items():
            latest_entry_dict[key] = str(value).replace(' ', '_')
        column_mapping = {v: k for k, v in latest_entry_dict.items()}
        filtered_mapping = {key: value for key, value in column_mapping.items() if key != 'NA'}
                # missing_columns = [col for col in filtered_mapping.keys() if col not in df_csv.columns]
        for key, value in latest_entry_dict.items():
            if value == "NA":
                latest_entry_dict[key] = key
        columns_to_keep = [col for col in latest_entry_dict.values() if col in df_csv.columns]
        df_csv = df_csv[columns_to_keep]

        df_csv.rename(columns=filtered_mapping, inplace=True)
        def format_wireless_number(number):
            pattern2 = r'^\d{3}\-\d{3}\-\d{4}$'
            if len(str(number)) <= 10:
                return
            if re.match(pattern2, str(number)):
                return number
            pattern = r'^\d{3}\.\d{3}\.\d{4}$'
            
            if re.match(pattern, str(number)):
                return str(number).replace('.','-')
            
            cleaned_number = str(number).replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
            cleaned_number = '-'.join(cleaned_number.split('-'))
            formatted_number = cleaned_number[:3] + "-" + cleaned_number[3:6] + "-" + cleaned_number[6:]
            return formatted_number
        
        formatted_wireless_numbers = []
        # print("****",df_csv.columns)
        for number in df_csv['wireless_number']:
            formatted_wireless_numbers.append(format_wireless_number(number))
        df_csv['wireless_number'] = formatted_wireless_numbers

    # Fetch distinct values using Django ORM
        unique_account_numbers = PdfDataTable.objects.values_list('account_number', flat=True).distinct()
        companies = PdfDataTable.objects.values_list('company', flat=True).distinct()
        sub_companies = PdfDataTable.objects.values_list('sub_company', flat=True).distinct()
        vendors = PdfDataTable.objects.values_list('vendor', flat=True).distinct()

        # Fetch bill_date for given parameters
        print("getting first")
        bill_date = BaseDataTable.objects.filter(
            company=self.company,
            sub_company=self.sub_company,
            vendor=self.vendor,
            accountnumber=self.account_number
        ).values_list('bill_date', flat=True).first()

        try:
            unique_account_numbers_list = list(unique_account_numbers)
            company_list = list(companies)
            vendor_list = list(vendors)
            sub_company_list = list(sub_companies)
            
            df_acc = df_csv['account_number'].iloc[0]
            if self.company in company_list:
                print('in1')
                if self.sub_company in sub_company_list:
                    print('in2')
                    if self.vendor in vendor_list:
                        print('in3')
                        if df_acc in unique_account_numbers_list:
                            checked_acc = df_acc
                            print('credentials matched')
                        else:
                            checked_acc = None
                    else:
                        checked_acc = None
                else:
                    checked_acc = None
            else:
                checked_acc = None

        except:
            if self.account_number in unique_account_numbers_list:
                checked_acc = self.account_number
            else:
                checked_acc = None

        df_csv['sub_company'] = self.sub_company
        columns = df_csv.columns.tolist()

        for _, row in df_csv.iterrows():
            wireless_number = row['wireless_number']
            
            # Prepare update dictionary
            update_data = {col: row[col] for col in columns if col != 'wireless_number' and pd.notnull(row[col])}
            # Update existing records
            UniquePdfDataTable.objects.filter(wireless_number=wireless_number).update(**update_data)
            # Insert if not exists
            if not UniquePdfDataTable.objects.filter(wireless_number=wireless_number).exists():
                print("type=",self.type)
                UniquePdfDataTable.objects.create(viewuploaded=self.instance, **row.to_dict())
                print("Data added to UniquePdfDataTable")
