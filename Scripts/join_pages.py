
import fitz 

def join_pages(path):
    doc = fitz.open(path)
    result = fitz.open()

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


path = "Bills/media/BanUploadBill/ATT_Mobility_MPP.pdf"
join_pages(path)