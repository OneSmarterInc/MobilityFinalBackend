import pandas as pd
import json
import time
from ..models import PdfDataTable, BaseDataTable, UniquePdfDataTable
import re

class OnBoardExcel:
    def __init__(self, buffer_data, instance, mapping_obj):

        self.instance = instance
        self.buffer_data = buffer_data
        self.type = type
        self.company = self.buffer_data['company'] if 'company' in self.buffer_data else None
        self.excel_csv_path = self.buffer_data['excel_csv_path'] if 'excel_csv_path' in self.buffer_data else None
        self.vendor = self.buffer_data['vendor'] if 'vendor' in self.buffer_data else None
        self.account_number = buffer_data['account_number'] if 'account_number' in self.buffer_data else None
        self.sub_company = self.buffer_data['sub_company'] if 'sub_company' in self.buffer_data else None
        self.mapping_data = self.buffer_data['mapping_json'] if 'mapping_json' in self.buffer_data else None
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

    def process():
        pass
