from background_task import background
import time
import json
# from .bp import ProcessBills
# from View.enterbill.bp import ProcessBills
from View.enterbill.ep import EnterBillProcessExcel
from View.models import ViewUploadBill
from celery import shared_task
from .newbillprocessor import ProcessBills
from sendmail import send_custom_email
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

    try:
        obj = ProcessBills(buffer_data=buffer_data_dict, instance=instance)
        obj.process()
    except Exception as e:
        print("Internal Server Error")
        instance.delete()

# @shared_task
def process_view_excel(buffer_data, instance_id):
    print("Processing view bills...")
    buffer_data_dict = json.loads(buffer_data)

    try:
        instance = ViewUploadBill.objects.get(id=instance_id)
    except ViewUploadBill.DoesNotExist:
        print(f"Error: BaseDataTable object with ID {instance_id} not found.")
        return {"message": f"Error: BaseDataTable object with ID {instance_id} not found.", "error": 1}

    
    try:
        obj = EnterBillProcessExcel(buffer_data=buffer_data_dict, instance=instance)
        obj.process_csv_from_buffer()
    except Exception as e:
        print("Internal Server Error")
        sub = "Internal Server Error"
        msg = f"""Error occur during processing pdf \n
            {e}
        """
        send_custom_email(receiver_mail="gauravdhale09@gmail.com", subject=sub, body=msg)
        instance.delete()


# @shared_task
# def process_view_bills(buffer_data, instance):
#     buffer_data_dict = json.loads(buffer_data)
#     # process_bills(buffer_data_dict, instance)
#     obj = ProcessBills(buffer_data=buffer_data_dict, instance=instance)
#     obj.process()
