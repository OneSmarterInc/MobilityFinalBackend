
import re
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image

# Regex for wireless number + "continues..."
pattern = re.compile(r"(\(?\d{3}\)?[-.]?\s?\d{3}[-.]?\d{4})\s+continues\.\.\.$")

def pdf_merge_with_continue(input_pdf, output_pdf):
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)

    # Convert PDF pages to images
    images = convert_from_path(input_pdf, dpi=200)

    merged_images = []
    skip_next = False

    for i in range(total_pages):
        if skip_next:
            skip_next = False
            continue

        text = reader.pages[i].extract_text() or ""
        text = text.strip()

        # Check regex match
        if pattern.search(text) and i + 1 < total_pages:
            img1, img2 = images[i], images[i + 1]

            # Create combined tall image
            width = max(img1.width, img2.width)
            height = img1.height + img2.height

            new_img = Image.new("RGB", (width, height), (255, 255, 255))
            new_img.paste(img1, (0, 0))
            new_img.paste(img2, (0, img1.height))

            merged_images.append(new_img)
            skip_next = True  # Skip the next page
        else:
            merged_images.append(images[i])

    # Save output PDF
    merged_images[0].save(
        output_pdf,
        save_all=True,
        append_images=merged_images[1:],
        resolution=100.0
    )

# Example usage
pdf_merge_with_continue("Bills/media/BanUploadBill/ATT_Mobility_MPP.pdf", "output.pdf")
