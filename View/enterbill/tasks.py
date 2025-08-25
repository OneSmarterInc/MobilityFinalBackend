from .newVprocessor import ProcessPdf2
from sendmail import send_custom_email
from celery import shared_task
import json
from View.models import ViewUploadBill


def get_error_message():
    return '''This is an official notification that your recent PDF processing request could not be completed. The failure was caused by an unforeseen issue with our server infrastructure.\n

    Our technical team has been alerted and is working diligently to restore service, and we will notify you as soon as the issue is resolved. In the meantime, we kindly ask that you resubmit your document after a few hours.\n

    We sincerely apologize for this service interruption and appreciate your cooperation.'''
import time
@shared_task
def verizon_att_enterBill_processor(buffer_data, instance_id,btype):
    buffer_data_dict = json.loads(buffer_data)

    try:
        instance = ViewUploadBill.objects.get(id=instance_id)
    except ViewUploadBill.DoesNotExist:
        print(f"Error: BaseDataTable object with ID {instance_id} not found.")
        return {"message": f"Error: BaseDataTable object with ID {instance_id} not found.", "error": 1}

    try:
        obj = ProcessPdf2(buffer_data=buffer_data_dict,instance=instance,btype=btype)
        check, msg, ProcessTime = obj.start_process()
        if check:
            instance.is_processed = True
            instance.save()
        
        if ProcessTime >= 60:
            ProcessTime = f"{ProcessTime / 60:.2f} minutes"
        else:
            ProcessTime = f"{ProcessTime:.2f} seconds"
        print("Process Time:", ProcessTime)
        
        sub = "SimpleTek Pdf PDF Bill Upload"
        pdf_filename = buffer_data_dict.get("pdf_filename")
        if pdf_filename:
            pdf_filename = pdf_filename.split("/")[-1]
        if not check:
            msg = get_error_message()
        else:
            msg = f"{msg}\nYour pdf {pdf_filename} took {ProcessTime} to process"
        send_custom_email(company= buffer_data_dict.get('company_name'),to=buffer_data_dict.get("email"), subject=sub, body_text=msg)
        if not check:
            instance.delete()
            send_custom_email(company= buffer_data_dict.get('company_name'),to="gauravdhale09@gmail.com", subject=sub, body_text=msg)
    except Exception as e:
        errormsg = get_error_message()
        print("Internal Server Error")
        sub = "SimpleTek PDF Upload-Internal Server Error"
        msg = f"""Error occur during processing pdf
            {e}
        """
        send_custom_email(company= buffer_data_dict.get('company_name'),to=buffer_data_dict.get("email"), subject=sub, body_text=errormsg)
        send_custom_email(company= buffer_data_dict.get('company_name'),to="gauravdhale09@gmail.com", subject=sub, body_text=msg)
        instance.delete()

from View.enterbill.ep import EnterBillProcessExcel
from .newbillprocessor import ProcessBills


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
        send_custom_email(company= buffer_data_dict.get('company'),to="gauravdhale09@gmail.com", subject=sub, body_text=msg)
        instance.delete()


# @shared_task
# def process_view_bills(buffer_data, instance):
#     buffer_data_dict = json.loads(buffer_data)
#     # process_bills(buffer_data_dict, instance)
#     obj = ProcessBills(buffer_data=buffer_data_dict, instance=instance)
#     obj.process()
