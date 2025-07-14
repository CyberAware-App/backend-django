import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.conf import settings
import os


class CertificateGenerator:
    """
    Generate PDF certificates for users who passed the final quiz
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for the certificate"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica'
        )
        
        # Name style
        self.name_style = ParagraphStyle(
            'CustomName',
            parent=self.styles['Heading2'],
            fontSize=20,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Content style
        self.content_style = ParagraphStyle(
            'CustomContent',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica'
        )
        
        # Footer style
        self.footer_style = ParagraphStyle(
            'CustomFooter',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.grey,
            fontName='Helvetica'
        )
    
    def generate_certificate_pdf(self, certificate_data):
        """
        Generate a PDF certificate
        
        Args:
            certificate_data (dict): Certificate information including user details
            
        Returns:
            bytes: PDF file content
        """
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build PDF content
        story = []
        
        # Add title
        title = Paragraph("Certificate of Completion", self.title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Add subtitle
        subtitle = Paragraph("This is to certify that", self.subtitle_style)
        story.append(subtitle)
        story.append(Spacer(1, 30))
        
        # Add user name
        name = Paragraph(certificate_data['user_name'], self.name_style)
        story.append(name)
        story.append(Spacer(1, 20))
        
        # Add completion text
        completion_text = Paragraph(
            f"has successfully completed the course with a score of {certificate_data['score']}%",
            self.content_style
        )
        story.append(completion_text)
        story.append(Spacer(1, 40))
        
        # Add issue date
        date_text = Paragraph(
            f"Issued on: {certificate_data['issued_date']}",
            self.content_style
        )
        story.append(date_text)
        story.append(Spacer(1, 60))
        
        # Add certificate ID
        cert_id_text = Paragraph(
            f"Certificate ID: {certificate_data['certificate_id']}",
            self.footer_style
        )
        story.append(cert_id_text)
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def generate_simple_certificate_pdf(self, certificate_data):
        """
        Generate a simpler PDF certificate with table layout
        
        Args:
            certificate_data (dict): Certificate information
            
        Returns:
            bytes: PDF file content
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        story = []
        
        # Title
        title = Paragraph("Certificate of Completion", self.title_style)
        story.append(title)
        story.append(Spacer(1, 30))
        
        # Certificate details table
        data = [
            ['Name:', certificate_data['user_name']],
            ['Email:', certificate_data['user_email']],
            ['Score:', f"{certificate_data['score']}%"],
            ['Issued Date:', certificate_data['issued_date']],
            ['Certificate ID:', certificate_data['certificate_id']],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Completion message
        completion_msg = Paragraph(
            "Congratulations! You have successfully completed the course requirements.",
            self.content_style
        )
        story.append(completion_msg)
        
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content 