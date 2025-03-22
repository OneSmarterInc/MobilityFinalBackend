# from background_task import background
# import time
# import json
# from .csv_processor import process_csv_from_buffer
# from .pdf_processor import process_pdf_from_buffer
# from .pp import ProcessPdf
# from ..models import OnboardBan
# from celery import shared_task




# # @background(schedule=3600)
# @shared_task
# def process_pdf_task(buffer_data, instance_id):
#     print("Processing PDF...")
#     buffer_data_dict = json.loads(buffer_data)
#     # process_pdf_from_buffer(buffer_data_dict)
#     try:
#         instance = OnboardBan.objects.filter(id=instance_id)[0]
#     except Exception as e:
#         print(f"Error occurred while retrieving instance: {str(e)}")
#         return {"message": f"Error occurred while retrieving instance: {str(e)}", "error":1}
#     obj = ProcessPdf(buffer_data=buffer_data_dict, instance=instance)
#     print(buffer_data)
#     obj.process_pdf_from_buffer()

from celery import shared_task
import json
from OnBoard.Ban.models import OnboardBan
from OnBoard.Ban.models import InventoryUpload
from OnBoard.Ban.Background.pp import ProcessPdf
from OnBoard.Ban.Background.cp import ProcessCsv


@shared_task
def process_pdf_task(buffer_data, instance_id):
    print("Processing PDF...")
    buffer_data_dict = json.loads(buffer_data)

    try:
        instance = OnboardBan.objects.get(id=instance_id)
    except OnboardBan.DoesNotExist:
        print(f"Error: OnboardBan object with ID {instance_id} not found.")
        return {"message": f"Error: OnboardBan object with ID {instance_id} not found.", "error": 1}

    obj = ProcessPdf(buffer_data=buffer_data_dict, instance=instance)
    print(buffer_data_dict)
    obj.process_pdf_from_buffer()


# @background(schedule=3600)
@shared_task
def process_csv(instance_id, buffer_data,type=None):
    print("Processing CSV...")
    buffer_data_dict = json.loads(buffer_data)

    try:
        if type and type == 'inventory':
            instance = InventoryUpload.objects.get(id=instance_id)
        else:
            instance = OnboardBan.objects.get(id=instance_id)
    except OnboardBan.DoesNotExist:
        print(f"Error: OnboardBan object with ID {instance_id} not found.")
        return {"message": f"Error: OnboardBan object with ID {instance_id} not found.", "error": 1}
    except InventoryUpload.DoesNotExist:
        print(f"Error: InventoryUpload object with ID {instance_id} not found.")
        return {"message": f"Error: InventoryUpload object with ID {instance_id} not found.", "error": 1}
    print(buffer_data_dict)
    obj = ProcessCsv(buffer_data=buffer_data_dict, instance=instance,type=type)
    obj.process_csv_from_buffer()