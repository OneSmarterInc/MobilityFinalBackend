from background_task import background
import time
import json
from .analysis_processor import process_analysis_pdf_from_buffer

# @background(schedule=3600)
def process_analysis_task(instance, buffer_data):
    print("def process_analysis_task")
    buffer_dict = json.loads(buffer_data)
    process_analysis_pdf_from_buffer(instance, buffer_dict)