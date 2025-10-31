from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, A5 # A3 is used for the page size
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import pandas as pd
import io


def add_header_footer(canvas_obj, doc):
    # Use the actual pagesize dimensions from the document, which is A3
    width, height = doc.pagesize 
    header_height = 45
    
    # Position the header 50 points down from the top edge
    y_pos = height - header_height - 50 
    
    # Draw the green rectangle across the full width of the page
    canvas_obj.setFillColorRGB(0.18, 0.55, 0.34)
    canvas_obj.rect(0, y_pos, width, header_height, fill=True, stroke=False)

    # Header Title
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica-Bold", 16)
    text_y = y_pos + header_height / 2 - 5
    # Center the title using the full page width
    canvas_obj.drawCentredString(width / 2, text_y, "Plan Savings Analysis Report")

    # Footer
    canvas_obj.setFont("Helvetica-Oblique", 9)
    canvas_obj.setFillColor(colors.gray)
    footer_text = f"Page {doc.page} | Generated on {datetime.now().strftime('%d %b %Y')}"
    # Center the footer using the full page width
    canvas_obj.drawCentredString(width / 2, 25, footer_text)


def create_savings_pdf(df, acc, bill_dates):
    buffer = io.BytesIO()

    # Replace None with 0 for numeric columns to prevent errors
    df["recommended_plan_savings"] = df["recommended_plan_savings"].fillna(0)
    df["recommended_plan_charges"] = df["recommended_plan_charges"].fillna(0)
    df["current_plan_charges"] = df["current_plan_charges"].fillna(0)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A3, # Set to A3 for a larger width (297mm vs A4's 210mm)
        rightMargin=30,
        leftMargin=30,
        topMargin=130,
        bottomMargin=50
    )
    elements = []
    styles = getSampleStyleSheet()

    # ---- Metadata summary ----
    max_savings = df["recommended_plan_savings"].max()
    avg_savings = df["recommended_plan_savings"].mean()
    avg_current_charges = df.get("current_plan_charges", pd.Series([0])).mean()

    avg_savings_percent = 0 if avg_current_charges is 0 else (avg_savings / avg_current_charges) * 100
    
    metadata = [
        ["Generated Date", datetime.now().strftime("%d %b %Y")],
        ["Account Number", acc]
    ]

    for i, bill_date in enumerate(bill_dates):
        metadata.append([f"Month {i+1}", f"{bill_date}"])
    
    metadata.extend([
        ["Total Records", len(df)],
        ["Highest Savings ($)", f"{max_savings:.2f}"],
        ["Total Savings (%)", f"{avg_savings_percent:.2f}"]])
    
    meta_table = Table(metadata)
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 20))

    # ---- Main Data Table ----
    header_data = [
        "User Name", "Wireless Number", "Current Plan", "Current Charges ($)",
        "Recommended Plan", "Recommended ($)", "Savings ($)"
    ]
    data = [header_data]

    for row in df.to_dict("records"):
        data.append([
            row.get("user_name", "--"),
            row.get("wireless_number", "--"),
            row.get("current_plan", "--"),
            f"{(row.get('current_plan_charges') or 0):.2f}",
            row.get("recommended_plan", "--"),
            f"{(row.get('recommended_plan_charges') or 0):.2f}",
            f"{(row.get('recommended_plan_savings') or 0):.2f}",
        ])

    table = Table(data, repeatRows=1)
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])

    # ---- Highlight rows with above-average savings ----
    # for i, row in enumerate(df.itertuples(), start=1):
    #     savings = row.recommended_plan_savings or 0
    #     if savings >= avg_savings:
    #         style.add("BACKGROUND", (-1, i), (-1, i), colors.lightgreen)

    table.setStyle(style)
    elements.append(table)
    
    # ----------------------------------------------------
    # ADDED: Note at the end of the table content flow
    # ----------------------------------------------------
    elements.append(Spacer(1, 10)) # Add a small space after the table
    
    note_text = "Note: This is an AI generated report"
    # Use 'Normal' style for the paragraph
    note_paragraph = Paragraph(note_text, styles["Normal"])
    
    # Customize the style for the note (optional but good practice)
    note_paragraph.style.fontSize = 9
    note_paragraph.style.fontName = 'Helvetica-Bold'
    note_paragraph.style.alignment = 0  # 0 for left alignment
    
    elements.append(note_paragraph)
    # ----------------------------------------------------


    doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    pdf_value = buffer.getvalue()
    buffer.close()

    return pdf_value


# Update the savings list with 'wireless_number' and 'user_name' data
savings = [
    # user_name present
    {"user_name": "Christopher Eime", "wireless_number": "314-365-7431", "current_plan": "Business Unlimited Smartphone", "current_plan_charges": 70, "recommended_plan": "Flex Business Data Device 2GB", "recommended_plan_charges": 31.5, "recommended_plan_savings": 38.5},
    # user_name missing (will default to "--")
    {"wireless_number": "5678", "current_plan": "Plan C", "current_plan_charges": 90.00, "recommended_plan": "Plan D", "recommended_plan_charges": 60.00, "recommended_plan_savings": 30.00},
    # user_name present
    {"user_name": "asmith", "wireless_number": "9012", "current_plan": "Plan E", "current_plan_charges": 80.00, "recommended_plan": "Plan F", "recommended_plan_charges": 55.00, "recommended_plan_savings": 25.00}
]

# Convert the example savings list into a pandas DataFrame
# create_savings_pdf(pd.DataFrame(savings*12), filename="example_savings_report.pdf")