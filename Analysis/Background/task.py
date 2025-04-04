import time
import json
from Analysis.Background.analysis_processor import process_analysis_pdf_from_buffer
from Analysis.models import Analysis
from celery import shared_task

@shared_task
def process_analysis_task(buffer_data, instance_id):
    print("def process_analysis_task")
    buffer_dict = json.loads(buffer_data)
    try:
        instance = Analysis.objects.get(id=instance_id)
    except Analysis.DoesNotExist:
        return {"message": f"Error: Analysis object with ID {instance_id} not found.", "error": 1}
    except Exception as e:
        return {"message":f"{str(e)}", "error":1}
    process_analysis_pdf_from_buffer(instance, buffer_dict)
