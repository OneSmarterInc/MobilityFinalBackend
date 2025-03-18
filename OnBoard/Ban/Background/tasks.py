from background_task import background
import time
import json
from .csv_processor import process_csv_from_buffer
from .pdf_processor import process_pdf_from_buffer

# @background(schedule=3600)
def process_csv(instance, buffer_data):
    print("Processing CSV...")
    buffer_data = str(buffer_data)
    buffer_data_dict = json.loads(buffer_data)
    print(buffer_data_dict)
    process_csv_from_buffer(instance, buffer_data_dict)

# @background(schedule=3600)
def process_pdf_task(buffer_data):
    print("Processing PDF...")
    buffer_data_dict = json.loads(buffer_data)
    process_pdf_from_buffer(buffer_data_dict)
