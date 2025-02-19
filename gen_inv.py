#!/usr/bin/env python3

# /// script
# dependencies = [
#   "reportlab"
# ]
# ///
from datetime import datetime, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_test_invoice():
    # Create the PDF document
    doc = SimpleDocTemplate(
        "test_invoice.pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Warning",
            textColor=colors.red,
            fontSize=12,
            alignment=1,  # Center alignment
        )
    )

    # Add warning header
    elements.append(Paragraph("TEST INVOICE - NOT A REAL DOCUMENT", styles["Warning"]))
    elements.append(Spacer(1, 20))

    # Company information
    elements.append(Paragraph("Test Company, Inc.", styles["Heading1"]))
    elements.append(Paragraph("123 Test Street", styles["Normal"]))
    elements.append(Paragraph("Demo City, TS 12345", styles["Normal"]))
    elements.append(Paragraph("contact@testcompany.test", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Invoice details
    invoice_date = datetime.now()
    due_date = invoice_date + timedelta(days=30)

    invoice_info = [
        ["Invoice Number:", "TEST-2025-0001"],
        ["Date:", invoice_date.strftime("%Y-%m-%d")],
        ["Due Date:", due_date.strftime("%Y-%m-%d")],
    ]

    t = Table(invoice_info, colWidths=[100, 150])
    t.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Bill To section
    elements.append(Paragraph("Bill To:", styles["Heading2"]))
    elements.append(Paragraph("Sample Customer", styles["Normal"]))
    elements.append(Paragraph("456 Demo Avenue", styles["Normal"]))
    elements.append(Paragraph("Test Town, TS 67890", styles["Normal"]))
    elements.append(Paragraph("customer@example.test", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Invoice items
    data = [
        ["Description", "Quantity", "Unit Price", "Amount"],
        ["Test Product Premium", "1", "$99.00", "$99.00"],
        ["Additional Services", "2", "$45.00", "$90.00"],
        ["", "", "Subtotal:", "$189.00"],
        ["", "", "Tax (10%):", "$18.90"],
        ["", "", "Total:", "$207.90"],
    ]

    table = Table(data, colWidths=[240, 75, 75, 75])
    table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -4), 1, colors.black),
                ("FONTNAME", (0, -3), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 40))

    # Footer warning
    elements.append(
        Paragraph(
            "This is test data generated for development purposes. Not a valid financial document.",
            styles["Warning"],
        )
    )

    # Build the PDF
    doc.build(elements)


if __name__ == "__main__":
    generate_test_invoice()
