"""
PDF Generator Utility

Creates printable PDF documents for student reports and fee receipts.
Uses ReportLab for PDF generation.
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
from io import BytesIO


# Try to register a nicer font if available (optional)
try:
    pdfmetrics.registerFont(TTFont('SegoeUI', 'segoeui.ttf'))
    FONT_NAME = 'SegoeUI'
except:
    FONT_NAME = 'Helvetica'


def generate_fee_receipt(fee_record, output_path):
    """
    Generate a PDF receipt for a fee payment.

    Args:
        fee_record (dict): Dictionary containing fee details with keys:
            - roll_no, student_name, term, total_amount, paid_amount,
            - due_date, last_payment_date (optional)
        output_path (str): Path where the PDF will be saved.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=72
        )
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontName=FONT_NAME,
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=12,
            spaceBefore=10,
            spaceAfter=5
        )
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10
        )

        # Header
        story.append(Paragraph("FEE RECEIPT", title_style))
        story.append(Spacer(1, 0.2*inch))

        # Institution details
        story.append(Paragraph("Student Management System", heading_style))
        story.append(Paragraph("123 Education Lane, Knowledge City", normal_style))
        story.append(Paragraph("Phone: +91 12345 67890 | Email: fees@sms.edu", normal_style))
        story.append(Spacer(1, 0.3*inch))

        # Receipt details
        receipt_no = f"RCP-{fee_record.get('roll_no', 'XXXX')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        date_str = datetime.now().strftime("%d %B %Y")

        data = [
            ["Receipt No:", receipt_no, "Date:", date_str],
            ["Student Roll No:", fee_record.get('roll_no', 'N/A'), "Student Name:", fee_record.get('student_name', 'N/A')],
            ["Term:", fee_record.get('term', 'N/A'), "Academic Year:", fee_record.get('academic_year', 'N/A')],
        ]

        table = Table(data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 2*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3*inch))

        # Fee breakdown
        total = fee_record.get('total_amount', 0.0)
        paid = fee_record.get('paid_amount', 0.0)
        due = total - paid

        fee_data = [
            ["Description", "Amount (₹)"],
            ["Total Fees", f"{total:,.2f}"],
            ["Amount Paid", f"{paid:,.2f}"],
            ["Balance Due", f"{due:,.2f}"],
        ]

        fee_table = Table(fee_data, colWidths=[3*inch, 2*inch])
        fee_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(fee_table)
        story.append(Spacer(1, 0.3*inch))

        # Payment details
        last_payment = fee_record.get('last_payment_date', 'N/A')
        due_date = fee_record.get('due_date', 'N/A')
        story.append(Paragraph(f"Last Payment Date: {last_payment}", normal_style))
        story.append(Paragraph(f"Due Date: {due_date}", normal_style))
        story.append(Spacer(1, 0.5*inch))

        # Signatures
        sig_data = [
            ["__________________________", "__________________________"],
            ["Student / Parent Signature", "Authorized Signatory"],
        ]
        sig_table = Table(sig_data, colWidths=[2.5*inch, 2.5*inch])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
        ]))
        story.append(sig_table)

        doc.build(story)
        return True

    except Exception as e:
        print(f"PDF generation error: {e}")
        return False


def generate_student_report(db_manager, roll_no, output_path, options=None):
    """
    Generate a comprehensive student report PDF.

    Args:
        db_manager: DatabaseManager instance.
        roll_no (str): Student roll number.
        output_path (str): Output file path.
        options (dict): Sections to include:
            - include_personal (bool)
            - include_attendance (bool)
            - include_fees (bool)
            - include_exams (bool)
            - include_graphs (bool)
            - include_charts (bool)

    Returns:
        bool: True if successful, False otherwise.
    """
    if options is None:
        options = {
            "include_personal": True,
            "include_attendance": True,
            "include_fees": True,
            "include_exams": True,
            "include_graphs": True,
            "include_charts": True,
        }

    try:
        # Import models here to avoid circular imports
        from database.student_model import StudentModel
        from database.attendance_model import AttendanceModel
        from database.fees_model import FeesModel
        from database.exam_model import ExamModel

        student_model = StudentModel(db_manager)
        attendance_model = AttendanceModel(db_manager)
        fees_model = FeesModel(db_manager)
        exam_model = ExamModel(db_manager)

        # Fetch data
        student = student_model.get_by_roll(roll_no)
        if not student:
            raise ValueError(f"Student {roll_no} not found.")

        attendance_summary = attendance_model.get_summary_by_roll(roll_no) if options.get("include_attendance") else {}
        fees_summary = fees_model.get_summary_by_roll(roll_no) if options.get("include_fees") else {}
        exams = exam_model.get_by_roll(roll_no) if options.get("include_exams") else []

        # Create PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=50, leftMargin=50,
            topMargin=50, bottomMargin=50
        )
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontName=FONT_NAME,
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=10,
            textColor=colors.HexColor('#1A237E')
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.grey
        )
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontName=FONT_NAME,
            fontSize=13,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor('#3949AB')
        )
        normal_style = ParagraphStyle(
            'Normal',
            parent=styles['Normal'],
            fontName=FONT_NAME,
            fontSize=10,
            spaceAfter=3
        )

        # Header
        story.append(Paragraph("STUDENT PROGRESS REPORT", title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%d %B %Y')}", subtitle_style))
        story.append(Spacer(1, 0.2*inch))

        # Personal Information
        if options.get("include_personal"):
            story.append(Paragraph("PERSONAL DETAILS", section_style))
            personal_data = [
                ["Roll Number:", student['Roll_No']],
                ["Full Name:", student['Name']],
                ["Email:", student['Email']],
                ["Gender:", student['Gender']],
                ["Contact:", student['Contact']],
                ["Date of Birth:", student['DOB']],
                ["Address:", student['Address']],
            ]
            personal_table = Table(personal_data, colWidths=[1.5*inch, 4*inch])
            personal_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(personal_table)
            story.append(Spacer(1, 0.2*inch))

        # Attendance Summary
        if options.get("include_attendance") and attendance_summary:
            story.append(Paragraph("ATTENDANCE SUMMARY", section_style))
            total = attendance_summary.get('total_days', 0)
            present = attendance_summary.get('present', 0)
            absent = attendance_summary.get('absent', 0)
            late = attendance_summary.get('late', 0)
            pct = attendance_summary.get('percentage', 0)

            att_data = [
                ["Total Days:", str(total)],
                ["Present:", f"{present} ({pct:.1f}%)"],
                ["Absent:", str(absent)],
                ["Late:", str(late)],
            ]
            att_table = Table(att_data, colWidths=[1.5*inch, 2*inch])
            att_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(att_table)
            story.append(Spacer(1, 0.2*inch))

        # Fees Status
        if options.get("include_fees") and fees_summary:
            story.append(Paragraph("FEES STATUS", section_style))
            total_fee = fees_summary.get('total_fee', 0.0)
            paid = fees_summary.get('paid', 0.0)
            due = fees_summary.get('due', 0.0)
            status = fees_summary.get('status', 'N/A')

            fee_data = [
                ["Total Fees:", f"₹{total_fee:,.2f}"],
                ["Paid Amount:", f"₹{paid:,.2f}"],
                ["Due Amount:", f"₹{due:,.2f}"],
                ["Status:", status],
            ]
            fee_table = Table(fee_data, colWidths=[1.5*inch, 2*inch])
            fee_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(fee_table)
            story.append(Spacer(1, 0.2*inch))

        # Exam Scores
        if options.get("include_exams") and exams:
            story.append(Paragraph("EXAMINATION RECORDS", section_style))
            if exams:
                # Group by subject for summary, or list all
                table_data = [["Subject", "Date", "Marks", "Percentage"]]
                for exam in exams:
                    pct = (exam['marks_obtained'] / exam['max_marks']) * 100 if exam['max_marks'] else 0
                    table_data.append([
                        exam['subject'],
                        exam.get('exam_date', 'N/A'),
                        f"{exam['marks_obtained']:.1f}/{exam['max_marks']:.1f}",
                        f"{pct:.1f}%"
                    ])

                exam_table = Table(table_data, colWidths=[1.8*inch, 1.2*inch, 1.2*inch, 1.2*inch])
                exam_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (2, 1), (3, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(exam_table)
                story.append(Spacer(1, 0.2*inch))

                # Performance Graph
                if options.get("include_graphs") and options.get("include_charts") and exams:
                    # Create a simple bar chart
                    fig, ax = plt.subplots(figsize=(6, 3))
                    subjects = list({e['subject'] for e in exams})
                    # Average percentage per subject
                    avg_scores = []
                    for subj in subjects:
                        subj_exams = [e for e in exams if e['subject'] == subj]
                        avg = sum((e['marks_obtained']/e['max_marks']*100) for e in subj_exams) / len(subj_exams)
                        avg_scores.append(avg)

                    ax.bar(subjects, avg_scores, color='#3949AB')
                    ax.set_ylabel('Average %')
                    ax.set_title('Subject-wise Performance')
                    ax.set_ylim(0, 100)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()

                    img_data = BytesIO()
                    plt.savefig(img_data, format='png', dpi=100)
                    plt.close(fig)
                    img_data.seek(0)

                    img = Image(img_data, width=5*inch, height=2.5*inch)
                    story.append(Spacer(1, 0.2*inch))
                    story.append(img)

        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("--- End of Report ---", normal_style))

        doc.build(story)
        return True

    except Exception as e:
        print(f"Report generation error: {e}")
        return False