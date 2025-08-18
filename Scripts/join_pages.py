
import fitz 

def join_pages(path):
    doc = fitz.open(path)
    result = fitz.open()
    page = doc[5]  # first page
    text = page.get_text()
    print(text)
    for i in range(0, len(doc), 2):
       
        page1 = doc[i]
        page2 = doc[i + 1] if i + 1 < len(doc) else None

        width = page1.rect.width
        height = page1.rect.height + (page2.rect.height if page2 else 0)

        new_page = result.new_page(width=width, height=height)

        new_page.show_pdf_page(fitz.Rect(0, 0, width, page1.rect.height), doc, i)

        if page2:
            new_page.show_pdf_page(
                fitz.Rect(0, page1.rect.height, width, height),
                doc,
                i + 1
            )
    result.save("output_pdf.pdf")


path = "Bills/media/BanUploadBill/ATT Mobility MPP.pdf"
join_pages(path)
from PyPDF2 import PdfReader
reader = PdfReader(path)

page_number = 5  # 0-based index
page = reader.pages[page_number]
text = page.extract_text()
print(text)