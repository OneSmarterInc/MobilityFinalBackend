import pandas as pd
import json
import time
from ..models import PdfDataTable, BaseDataTable, UniquePdfDataTable, BaselineDataTable, PortalInformation
import re


class ProcessCSVOnboard:
    def __init__(self, buffer_data,instance,uploadtype=None):
        print("init")
        self.instance = instance
        self.buffer_data = json.loads(buffer_data) if isinstance(buffer_data, str) else buffer_data
        self.type = uploadtype
        self.company = self.buffer_data.get('company')
        self.vendor = self.buffer_data.get('vendor')
        self.account_number = self.buffer_data.get('account_number')
        self.sub_company = self.buffer_data.get('sub_company')
        self.mapping_data = self.buffer_data.get('mapping_json')
        self.location_csv_path = self.buffer_data.get('location_csv_path')
        self.excel_csv_path = self.buffer_data.get('excel_csv_path')
        self.csv_path = self.buffer_data.get('csv_path')
        self.entry_type = self.buffer_data.get('entry_type')
        self.master_account = self.buffer_data.get('master_account')
        self.location = self.buffer_data.get('location')
        self.month = self.buffer_data.get('month')
        self.email = self.buffer_data.get('email')
        self.year = self.buffer_data.get('year')

        print("init complete")

    def process(self):
        if self.csv_path:
            self.process_csv_data()
        elif self.location_csv_path:
            self.process_location_csv_data()
        elif self.excel_csv_path:
            self.process_excel_csv_data()

    def format_wireless_number(self, number):
        print("number===",number)
        
        if len(str(number)) <= 10:
            return
        pattern2 = r'^\d{3}\-\d{3}\-\d{4}$'
        if re.match(pattern2, str(number)):
            return number
        pattern = r'^\d{3}\.\d{3}\.\d{4}$'
        
        if re.match(pattern, str(number)):
            return str(number).replace('.','-')
        
        cleaned_number = str(number).replace("(", "").replace(")", "").replace("-", "").replace(" ", "")
        cleaned_number = '-'.join(cleaned_number.split('-'))
        formatted_number = cleaned_number[:3] + "-" + cleaned_number[3:6] + "-" + cleaned_number[6:]
        return formatted_number

    def process_excel_csv_data(self):
        df_csv = pd.read_excel(self.excel_csv_path)

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
        
        rw = df_csv.iloc[0]
        base_dict = rw.to_dict()
        print("base_dict======", base_dict)

        file_vendor = base_dict.get('vendor')
        file_account_number = base_dict.get('account_number')

        if file_vendor != self.vendor:
            return {"message":f"Input vendor {self.vendor} not matched with excel vendor {file_vendor}!", 'code':1}
        print("vendor checked")

        print(file_account_number, self.account_number)
        
        if BaseDataTable.objects.filter(accountnumber=file_account_number).exists():
            return {'code':1, 'account_number':file_account_number, 'message':'account number already exists!'}
        
        # if str(file_account_number) != str(self.account_number):
        #     return {"message":f"Input account number {self.account_number} not matched with excel account number {file_account_number}!", 'code':1}
        print("existance checked")
        base_dict['company'] = self.company
        base_dict['vendor'] = self.vendor
        base_dict['sub_company'] = self.sub_company
        base_dict['accountnumber'] = base_dict.get('account_number')
        base_dict['Entry_type'] = self.entry_type
        base_dict['location'] = self.location
        base_dict['master_account'] = self.master_account

        keys_to_keep = ['company', 'vendor', 'sub_company', 'accountnumber', 'Entry_type', 'location', 'master_account']
        b_dict = {key: base_dict[key] for key in keys_to_keep if key in base_dict}

        # Insert into BaseDataTable
        if self.type and self.type == 'inventory':
            base = BaseDataTable.objects.create(inventory=self.instance, **b_dict)
        else:
            base = BaseDataTable.objects.create(banOnboarded=self.instance,**b_dict)
        
        print("Data added to BaseDataTable")
        self.account_number = base.accountnumber
        df_csv['wireless_number'] = df_csv['wireless_number'].apply(self.format_wireless_number)
        df_csv_dict = df_csv.to_dict(orient='records')
        for item in df_csv_dict:
            item['company'] = self.company
            item['vendor'] = self.vendor
            item['sub_company'] = self.sub_company
            item['account_number'] = self.account_number
            item['entry_type'] = self.entry_type
        # Bulk insert into UniquePDFDataTable
        UniquePdfDataTable.objects.bulk_create([UniquePdfDataTable(banOnboarded=self.instance,**item) for item in df_csv_dict])
        print("Data added to UniquePdfDataTable")

        df_csv = pd.DataFrame(df_csv_dict)
        df_csv = df_csv.rename(columns={'wireless_number': 'Wireless_number'})

        df_csv_dict = df_csv.to_dict(orient='records')
        
        model_fields = [field.name for field in BaselineDataTable._meta.get_fields() if field.concrete and not field.auto_created]

        # Prepare clean items
        clean_items = [
            BaselineDataTable(banOnboarded=self.instance, **{k: v for k, v in item.items() if k in model_fields})
            for item in df_csv_dict
        ]

        BaselineDataTable.objects.bulk_create(clean_items)
        self.save_to_portal_info({'Website':None})
        return {'code' : 0, 'message':f"Excel file with account number {file_account_number} onboarded successfully!"}


    def save_to_portal_info(self, data):
        obj = PortalInformation.objects.create(
            URL = data['Website'] if 'Website' in data else None,
            banOnboarded = self.instance,
            Customer_Name = self.sub_company,
            Vendor = self.vendor,
            Account_number = self.account_number,
            User_email_id = self.email,
        )
        obj.save()
    def process_location_csv_data(self):
        df_csv = pd.read_excel(self.location_csv_path)
        
        # Clean up the column names in the CSV
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

        # Connect to the database
        import time
        from Location.models import Location as AddLocation

        def fetch_latest_entry():
            return AddLocation.objects.order_by('-id').first()

        def is_location_done(entry_dict):
            return entry_dict.get('location_type') == 'Done'

        while True:
            # Fetch the latest mapping entry
            latest_entry = fetch_latest_entry()

            # Check if no entry is returned
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
        print("Processing CSV data")
        df_csv = pd.read_excel(self.csv_path)
        df_csv.columns = df_csv.columns.str.strip()
        print("df_csv columns before cleaning: ", df_csv)
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

        
        latest_entry_dict =  json.loads(json.dumps(self.mapping_data))

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
        for number in df_csv['wireless_number']:
            formatted_wireless_numbers.append(format_wireless_number(number)) if number else None
            
        df_csv['wireless_number'] = formatted_wireless_numbers

        unique_account_numbers = PdfDataTable.objects.values_list('account_number', flat=True).distinct()
        companies = PdfDataTable.objects.values_list('company', flat=True).distinct()
        sub_companies = PdfDataTable.objects.values_list('sub_company', flat=True).distinct()
        vendors = PdfDataTable.objects.values_list('vendor', flat=True).distinct()

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
            if wireless_number and not UniquePdfDataTable.objects.filter(wireless_number=wireless_number).exists():
                print("type=",self.type)
                if self.type and self.type == 'inventory':
                    UniquePdfDataTable.objects.create(inventory=self.instance, **row.to_dict())
                else:
                    UniquePdfDataTable.objects.create(banOnboarded=self.instance,**row.to_dict())
                print("Data added to UniquePdfDataTable")

class ProcessCsv:
    def __init__(self, buffer_data,instance,type=None):
        self.instance = instance
        self.buffer_data = buffer_data
        self.type = type
        self.company = self.buffer_data['company'] if 'company' in self.buffer_data else None
        self.csv_path = self.buffer_data['csv_path'] if 'csv_path' in self.buffer_data else None
        self.location_csv_path = self.buffer_data['location_csv_path'] if 'location_csv_path' in self.buffer_data else None
        self.excel_csv_path = self.buffer_data['excel_csv_path'] if 'excel_csv_path' in self.buffer_data else None
        self.vendor = self.buffer_data['vendor'] if 'vendor' in self.buffer_data else None
        self.account_number = buffer_data['account_number'] if 'account_number' in self.buffer_data else None
        self.sub_company = self.buffer_data['sub_company'] if 'sub_company' in self.buffer_data else None
        self.mapping_data = self.buffer_data['mapping_json'] if 'mapping_json' in self.buffer_data else None
        self.email = self.buffer_data['email'] if 'email' in self.buffer_data else None
        if 'entry_type' in self.buffer_data:
            self.entry_type = self.buffer_data['entry_type'] 
        else:
            self.entry_type = None
        if 'location' in self.buffer_data:
            self.location = self.buffer_data['location']
        else:
            self.location = None
        if 'master_account' in self.buffer_data:
            self.master_account = self.buffer_data['master_account']
        else:
            self.master_account = None

    
    

    def process_csv_from_buffer(self):
        if self.csv_path:
            print("csv_path: " + self.csv_path)
            self.process_csv_data()
        elif self.location_csv_path:
            loc_csv_path = self.buffer_data['location_csv_path']
            self.process_location_csv_data(loc_csv_path)
        elif self.excel_csv_path:
            ex_path = self.buffer_data['excel_csv_path']
            self.process_excel_csv_data(ex_path)
    
    def process_excel_csv_data(self, csv_path):
        df_csv = pd.read_excel(csv_path)

        df_csv.columns = df_csv.columns.str.strip()
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')
        
    
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
            
            

            rw = df_csv.iloc[0]
            base_dict = rw.to_dict()
            print("base_dict======", base_dict)

           
            base_dict['company'] = self.company
            base_dict['vendor'] = self.vendor
            base_dict['sub_company'] = self.sub_company
            base_dict['accountnumber'] = base_dict['account_number']
            base_dict['Entry_type'] = self.entry_type
            base_dict['location'] = self.location
            base_dict['master_account'] = self.master_account
            
            keys_to_keep = ['company', 'vendor', 'sub_company', 'accountnumber', 'Entry_type', 'location', 'master_account']
            b_dict = {key: base_dict[key] for key in keys_to_keep if key in base_dict}
            
            if BaseDataTable.objects.filter(accountnumber=b_dict['accountnumber']).exists():
                return f"Accoount number {b_dict['accountnumber']} already exists!"
            # Insert into BaseDataTable
            if self.type and self.type == 'inventory':
                base = BaseDataTable.objects.create(inventory=self.instance, **b_dict)
            else:
                base = BaseDataTable.objects.create(banOnboarded=self.instance,**b_dict)
           
            print("Data added to BaseDataTable")
            self.account_number = base.accountnumber
            df_csv['wireless_number'] = df_csv['wireless_number'].apply(self.format_wireless_number)
            df_csv_dict = df_csv.to_dict(orient='records')
            for item in df_csv_dict:
                item['company'] = self.company
                item['vendor'] = self.vendor
                item['sub_company'] = self.sub_company
                item['account_number'] = self.account_number
                item['entry_type'] = self.entry_type
            # Bulk insert into UniquePDFDataTable
            UniquePdfDataTable.objects.bulk_create([UniquePdfDataTable(banOnboarded=self.instance,**item) for item in df_csv_dict])
            print("Data added to UniquePdfDataTable")

            df_csv = pd.DataFrame(df_csv_dict)
            df_csv = df_csv.rename(columns={'wireless_number': 'Wireless_number'})

            df_csv_dict = df_csv.to_dict(orient='records')
            
            model_fields = [field.name for field in BaselineDataTable._meta.get_fields() if field.concrete and not field.auto_created]

            # Prepare clean items
            clean_items = [
                BaselineDataTable(banOnboarded=self.instance, **{k: v for k, v in item.items() if k in model_fields})
                for item in df_csv_dict
            ]

            BaselineDataTable.objects.bulk_create(clean_items)
            print("Data added to BaselineTable")
            self.save_to_portal_info({'Website':None})
        process_data(self.mapping_data, df_csv, self.company, self.vendor, self.sub_company, self.account_number, self.entry_type, self.location, self.master_account)
    def save_to_portal_info(self, data):
        obj = PortalInformation.objects.create(
            URL = data['Website'] if 'Website' in data else None,
            banOnboarded = self.instance,
            Customer_Name = self.sub_company,
            Vendor = self.vendor,
            Account_number = self.account_number,
            User_email_id = self.email,
        )
        obj.save()
    def process_location_csv_data(self, csv_path):
        # Load the Excel file into a pandas DataFrame
        df_csv = pd.read_excel(csv_path)
        
        # Clean up the column names in the CSV
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

        # Connect to the database
        import time
        from Location.models import Location as AddLocation

        def fetch_latest_entry():
            return AddLocation.objects.order_by('-id').first()

        def is_location_done(entry_dict):
            return entry_dict.get('location_type') == 'Done'

        while True:
            # Fetch the latest mapping entry
            latest_entry = fetch_latest_entry()

            # Check if no entry is returned
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
        print("Processing CSV data")
        df_csv = pd.read_excel(self.csv_path)
        df_csv.columns = df_csv.columns.str.strip()
        print("df_csv columns before cleaning: ", df_csv)
        df_csv.columns = df_csv.columns.str.strip().str.replace('-', '').str.replace(r'\s+', ' ', regex=True).str.replace(' ', '_')

        
        latest_entry_dict =  json.loads(json.dumps(self.mapping_data))

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
        for number in df_csv['wireless_number']:
            formatted_wireless_numbers.append(format_wireless_number(number)) if number else None
            
        df_csv['wireless_number'] = formatted_wireless_numbers

        unique_account_numbers = PdfDataTable.objects.values_list('account_number', flat=True).distinct()
        companies = PdfDataTable.objects.values_list('company', flat=True).distinct()
        sub_companies = PdfDataTable.objects.values_list('sub_company', flat=True).distinct()
        vendors = PdfDataTable.objects.values_list('vendor', flat=True).distinct()

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
            if wireless_number and not UniquePdfDataTable.objects.filter(wireless_number=wireless_number).exists():
                print("type=",self.type)
                if self.type and self.type == 'inventory':
                    UniquePdfDataTable.objects.create(inventory=self.instance, **row.to_dict())
                else:
                    UniquePdfDataTable.objects.create(banOnboarded=self.instance,**row.to_dict())
                print("Data added to UniquePdfDataTable")
