from background_task import background
import time
import json
from .billprocessor import process_bills

# @background(schedule=3600)
def process_view_bills(buffer_data, instance):
    buffer_data_dict = json.loads(buffer_data)
    process_bills(buffer_data_dict, instance)