from fpdf import FPDF
import pandas as pd
from datetime import datetime


# ------------------------------------------------------------
# Custom PDF class extending FPDF to add headers and footers
# ------------------------------------------------------------
class PDF(FPDF):
    def header(self):
        """
        This function automatically runs at the top of every new page.
        We use it to create a consistent, professional-looking header.
        """
        # Set a blue background bar at the top of the page
        self.set_fill_color(30, 144, 255)  # RGB color (Dodger Blue)
        self.rect(0, 0, 210, 20, 'F')      # Draw rectangle (x=0, y=0, width=210mm, height=15mm)

        # Set font and text color for the header text
        self.set_text_color(255, 255, 255)  # White text
        self.set_font('Arial', 'B', 14)     # Bold Arial font, size 14

        # Print the title centered
        self.cell(0, 1, 'Analysis Chats Report', ln=True, align='C')

        # Add a little space below the header bar
        self.ln(12)

        # Reset text color back to black for body content
        self.set_text_color(0, 0, 0)

    def footer(self):
        """
        This function automatically runs at the bottom of every page.
        We use it to add page numbers and a generated date/time stamp.
        """
        self.set_y(-15)                      # Move 15mm from the bottom
        self.set_font('Arial', 'I', 8)       # Italic, small font for footer
        self.set_text_color(100, 100, 100)   # Gray color text for footer

        # Add page number and generation date
        self.cell(0,10,f'Page {self.page_no()} | Generated on {datetime.now().strftime("%d %b %Y")}',0,0,'C')


# ------------------------------------------------------------
# Function to generate a styled PDF from chat dataframe
# ------------------------------------------------------------
def convert_chats_to_pdf(chatdf, acc, bill_dates):
    """
    Converts a pandas DataFrame containing chat Q&A into a visually appealing
    technical-style PDF with metadata, consistent formatting, and light styling.
    """

    # Initialize our custom PDF class
    pdf = PDF()
    pdf.add_page()  # Add the first page (header() runs automatically)

    # ----------------------------
    # Technical Metadata Section
    # ----------------------------
    pdf.set_font('Courier', '', 11)  # Monospaced font for technical style
    pdf.set_text_color(50, 50, 50)

    # Add a shaded background box for metadata
    # pdf.set_fill_color(245, 245, 245)
    # pdf.cell(0, 8, "SYSTEM METADATA", ln=True, align='L', fill=True)
    # pdf.ln(3)

    # Key-value format like logs or technical headers
    metadata = [
        ("Account Number", acc),

    ]
    for i, bill_date in enumerate(bill_dates):
        metadata.append([f"Month {i+1}", f"{bill_date}"])
    for key, value in metadata:
        pdf.cell(50, 8, f"{key}:", border=0)
        pdf.cell(0, 8, value, ln=True)
    pdf.ln(6)

    # Horizontal line separator
    pdf.set_draw_color(160, 160, 160)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # ----------------------------
    # Chats Section (Main Technical Content)
    # ----------------------------
    pdf.set_font('Courier', '', 10)  # Monospaced font for Q&A (developer/log style)
    pdf.set_text_color(0, 0, 0)

    # ----------------------------
    # Chats Section (Main Content)
    # ----------------------------
    for index, row in chatdf.iterrows():
        # --- Question Formatting ---
        pdf.set_font('Arial', 'B', 11)           # Bold font for questions
        pdf.set_text_color(30, 144, 255)         # Blue color for questions
        pdf.multi_cell(0, 8, f"{index+1}: {row['question']}")  # Multi-cell handles long lines automatically

        # --- Answer Formatting ---
        pdf.set_font('Arial', '', 11)            # Normal font for answers
        pdf.set_text_color(0, 0, 0)              # Black text for answer
        pdf.set_fill_color(245, 245, 245)        # Light gray background box
        pdf.multi_cell(0, 8, f"A: {row['response']}", fill=True)

        # --- Spacing & Divider ---
        pdf.ln(5)                                # Space between chats
        pdf.set_draw_color(220, 220, 220)        # Lighter gray for divider
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # Horizontal separator
        pdf.ln(5)                                # Space after divider

    # ----------------------------
    # Save the PDF file
    # ----------------------------
    pdf.output("analysis_chats.pdf")  # Save PDF in the current directory

    # return the PDF object in case further manipulation is needed
    return pdf.output(dest='S').encode('latin1')

# ------------------------------------------------------------
# Example Usage: Sample chat data
# ------------------------------------------------------------
chats = [
    {"question": "What is the capital of France?", "response": "The capital of France is Paris."},
    {"question": "What is the largest planet in our solar system?", "response": "The largest planet is Jupiter."},
    {"question": "Who wrote 'To Kill a Mockingbird'?", "response": "Harper Lee wrote 'To Kill a Mockingbird'."}
]

# Convert the example chat list into a pandas DataFrame
# convert_chats_to_pdf(pd.DataFrame(chats*12))
