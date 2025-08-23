
import google.generativeai as genai

genai.configure(api_key="AIzaSyBpjOEwkB7bIV5s0CYgXt0wpiXzCJil7pQ")

uploaded_file = genai.upload_file(path="Bills/media/BanUploadBill/ATT Mobility MPP.pdf", display_name="My PDF Report")
print(f"Uploaded file '{uploaded_file.display_name}' as: {uploaded_file.uri}")



prompt = "In dictionary format give Account number, Invoice number, bill date and due date"
model = genai.GenerativeModel('gemini-1.5-pro')

response = model.generate_content([uploaded_file, prompt])
print(response)
print(response.text)

genai.delete_file(name=uploaded_file.name)