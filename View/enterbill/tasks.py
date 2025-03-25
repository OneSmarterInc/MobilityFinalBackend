from background_task import background
import time
import json
from .billprocessor import process_bills
# from .bp import ProcessBills
from View.enterbill.bp import ProcessBills
from View.models import ViewUploadBill
from celery import shared_task

# @background(schedule=3600)
@shared_task
def process_view_bills(buffer_data, instance_id):
    print("Processing view bills...")
    buffer_data_dict = json.loads(buffer_data)

    try:
        instance = ViewUploadBill.objects.get(id=instance_id)
    except ViewUploadBill.DoesNotExist:
        print(f"Error: BaseDataTable object with ID {instance_id} not found.")
        return {"message": f"Error: BaseDataTable object with ID {instance_id} not found.", "error": 1}

    obj = ProcessBills(buffer_data=buffer_data_dict, instance=instance)
    obj.process()


# @shared_task
# def process_view_bills(buffer_data, instance):
#     buffer_data_dict = json.loads(buffer_data)
#     # process_bills(buffer_data_dict, instance)
#     obj = ProcessBills(buffer_data=buffer_data_dict, instance=instance)
#     obj.process()
