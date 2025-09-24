import time
import json
from Analysis.Background.analysis_processor import process_analysis_pdf_from_buffer
from Analysis.models import Analysis, MultipleFileUpload
from celery import shared_task
from sendmail import send_custom_email, send_generic_mail
from .NewProcessor import AnalysisProcessor
from .multipleFileProcessor import MultipleFileProcessor

def get_error_message():
    return '''This is an official notification that your recent PDF processing request could not be completed. The failure was caused by an unforeseen issue with our server infrastructure.\n

    Our technical team has been alerted and is working diligently to restore service, and we will notify you as soon as the issue is resolved. In the meantime, we kindly ask that you resubmit your document after a few hours.\n

    We sincerely apologize for this service interruption and appreciate your cooperation.'''

@shared_task
def Process_Analysis_PDF(buffer_data, instance_id):
    buffer_data_dict = json.loads(buffer_data) if isinstance(buffer_data,str) else buffer_data
    email = buffer_data_dict.get('user_email')

    try:
        instance = Analysis.objects.get(id=instance_id)
    except Analysis.DoesNotExist:
        print(f"Error: Analysis object with ID {instance_id} not found.")
        return {"message": f"Error: Analysis object with ID {instance_id} not found.", "error": 1}

    try:
        obj = AnalysisProcessor(instance=instance, buffer_data=buffer_data)
        check, Smsg, ProcessTime = obj.process()
        print("msg==",Smsg)
        if check:
            instance.is_processed = True
            instance.save()

        if ProcessTime >= 60:
            ProcessTime = f"{ProcessTime / 60:.2f} minutes"
        else:
            ProcessTime = f"{ProcessTime:.2f} seconds"
        print("Process Time:", ProcessTime)
        
        sub = "PDF Analysis"
        pdf_filename = buffer_data_dict.get("pdf_filename")
        if pdf_filename:
            pdf_filename = pdf_filename.split("/")[-1]
        if not check:
            msg = get_error_message()
        else:
            msg = f"{Smsg}\nYour pdf {pdf_filename} took {ProcessTime} to process"
        send_generic_mail(receiver_mail=email, subject=sub, body=msg)
        if not check:
            if instance and instance.pk: instance.delete()
            send_generic_mail(receiver_mail="gauravdhale09@gmail.com", subject=sub, body=f"{msg}\nReason-{Smsg}")
    except Exception as e:
        print(e)
        errormsg = get_error_message()
        print("Internal Server Error")
        sub = "PDF Analysis-Internal Server Error"
        msg = f"""Error occur during processing pdf
            {e}
        """
        send_generic_mail(receiver_mail=email, subject=sub, body=errormsg)        
        send_generic_mail(receiver_mail="gauravdhale09@gmail.com", subject=sub, body=msg)
        if instance and instance.pk: instance.delete()

@shared_task
def Process_multiple_pdfs(buffer_data, instance_id):
    buffer_data_dict = json.loads(buffer_data) if isinstance(buffer_data,str) else buffer_data
    email = buffer_data_dict.get('user_email')
    try:
        instance = MultipleFileUpload.objects.get(id=instance_id)
    except Analysis.DoesNotExist:
        print(f"Error: Analysis object with ID {instance_id} not found.")
        return {"message": f"Error: Analysis object with ID {instance_id} not found.", "error": 1}
    try:
        obj = MultipleFileProcessor(buffer_data=buffer_data, instance=instance)
        check, Smsg, ProcessTime, code = obj.process()
        print("msg==",Smsg)
        if check:
            instance.is_processed = True
            instance.save()

        if ProcessTime >= 60:
            ProcessTime = f"{ProcessTime / 60:.2f} minutes"
        else:
            ProcessTime = f"{ProcessTime:.2f} seconds"
        print("Process Time:", ProcessTime)
        
        sub = "PDF Analysis"
        pdf_filename = buffer_data_dict.get("pdf_filename")
        if pdf_filename:
            pdf_filename = pdf_filename.split("/")[-1]
        if not check:
            if code == 0:
                msg = get_error_message()
            else:
                msg = f"Unable to process your files\n{Smsg}"
        else:
            msg = f"{Smsg}\nYour pdf {pdf_filename} took {ProcessTime} to process"
            
        send_generic_mail(receiver_mail=email, subject=sub, body=msg)
        if not check:
            if instance and instance.pk: instance.delete()
            send_generic_mail(receiver_mail="gauravdhale09@gmail.com", subject=sub, body=f"{msg}\nReason-{Smsg}")

    except Exception as e:
        print(e)
        errormsg = get_error_message()
        print("Internal Server Error")
        sub = "PDF Analysis-Internal Server Error"
        msg = f"""Error occur during processing pdf
            {e}
        """
        send_generic_mail(receiver_mail=email, subject=sub, body=errormsg)        
        send_generic_mail(receiver_mail="gauravdhale09@gmail.com", subject=sub, body=msg)
        if instance and instance.pk: instance.delete()