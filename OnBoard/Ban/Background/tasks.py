

def get_error_message():
    return '''This is an official notification that your recent PDF processing request could not be completed. The failure was caused by an unforeseen issue with our server infrastructure.\n

    Our technical team has been alerted and is working diligently to restore service, and we will notify you as soon as the issue is resolved. In the meantime, we kindly ask that you resubmit your document after a few hours.\n

    We sincerely apologize for this service interruption and appreciate your cooperation.'''

from celery import shared_task
import json
from OnBoard.Ban.models import OnboardBan
from OnBoard.Ban.models import InventoryUpload

from OnBoard.Ban.Background.cp import ProcessCSVOnboard
from sendmail import send_custom_email
from OnBoard.Ban.Background.pp2 import ProcessPdf2
import time
@shared_task
def verizon_att_onboardPDF_processor(buffer_data, instance_id,btype):
    buffer_data_dict = json.loads(buffer_data)

    try:
        instance = OnboardBan.objects.get(id=instance_id)
    except OnboardBan.DoesNotExist:
        print(f"Error: OnboardBan object with ID {instance_id} not found.")
        return {"message": f"Error: OnboardBan object with ID {instance_id} not found.", "error": 1}

    try:
        obj = ProcessPdf2(buffer_data=buffer_data_dict,instance=instance,btype=btype)
        check, msg, ProcessTime = obj.start_process()

        if ProcessTime >= 60:
            ProcessTime = f"{ProcessTime / 60:.2f} minutes"
        else:
            ProcessTime = f"{ProcessTime:.2f} seconds"
        print("Process Time:", ProcessTime)
        
        sub = "SimpleTek Pdf Onboard"
        pdf_filename = buffer_data_dict.get("pdf_filename")
        if pdf_filename:
            pdf_filename = pdf_filename.split("/")[-1]
        if not check:
            msg = get_error_message()
        else:
            msg = f"{msg}\nYour pdf {pdf_filename} took {ProcessTime} to process"
        send_custom_email(receiver_mail=buffer_data_dict.get("user_email"), subject=sub, body=msg)
        if not check:
            instance.delete()
            send_custom_email(receiver_mail="gauravdhale09@gmail.com", subject=sub, body=msg)
    except Exception as e:
        errormsg = get_error_message()
        print("Internal Server Error")
        sub = "SimpleTek PDF Onboard-Internal Server Error"
        msg = f"""Error occur during processing pdf
            {e}
        """
        send_custom_email(receiver_mail=buffer_data_dict.get("user_email"), subject=sub, body=errormsg)
        send_custom_email(receiver_mail="gauravdhale09@gmail.com", subject=sub, body=msg)
        instance.delete()
    
from OnBoard.Ban.Background.pp import ProcessPdf
@shared_task
def process_pdf_task(buffer_data, instance_id):
    print("Processing PDF...")
    buffer_data_dict = json.loads(buffer_data)

    try:
        instance = OnboardBan.objects.get(id=instance_id)
    except OnboardBan.DoesNotExist:
        print(f"Error: OnboardBan object with ID {instance_id} not found.")
        return {"message": f"Error: OnboardBan object with ID {instance_id} not found.", "error": 1}

    try:
        obj = ProcessPdf(buffer_data=buffer_data_dict, instance=instance)
        obj.process_pdf_from_buffer()
    except Exception as e:
        print("Internal Server Error")
        sub = "Internal Server Error"
        msg = f"""Error occur during processing pdf \n
            {e}
        """
        send_custom_email(receiver_mail="gauravdhale09@gmail.com", subject=sub, body=msg)
        instance.delete()


# @background(schedule=3600)
# @shared_task
def process_csv(instance_id, buffer_data,type=None):
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
    

    try:
        obj = ProcessCSVOnboard(buffer_data=buffer_data_dict, instance=instance,uploadtype=type)
        process = obj.process_csv_data()
        return process
    except Exception as e:
        print("Internal Server Error")
        instance.delete()
        return {"message": f"{e}", "code": 1}
    
