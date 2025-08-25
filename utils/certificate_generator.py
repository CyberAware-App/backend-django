import io
from reportlab.lib.pagesizes import letter, A4, landscape
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
        # Palette (must be defined before styles reference them)
        self.primary_orange = colors.Color(1.0, 0.45, 0.0)  # vivid orange
        self.dark_navy = colors.HexColor('#0B1F3A')
        self.light_grey = colors.HexColor('#F4F5F7')
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for the certificate"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=36,
            leading=40,
            spaceAfter=16,
            alignment=TA_CENTER,
            textColor=self.dark_navy,
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=self.dark_navy,
            fontName='Helvetica'
        )
        
        # Name style
        self.name_style = ParagraphStyle(
            'CustomName',
            parent=self.styles['Heading2'],
            fontSize=28,
            spaceAfter=8,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        # Content style
        self.content_style = ParagraphStyle(
            'CustomContent',
            parent=self.styles['Normal'],
            fontSize=13,
            leading=18,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica'
        )

        # Award Title (big bold line under declaration)
        self.award_title_style = ParagraphStyle(
            'AwardTitle',
            parent=self.styles['Heading2'],
            fontSize=24,
            leading=28,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=self.dark_navy,
            fontName='Helvetica-Bold'
        )
        
        # Footer style
        self.footer_style = ParagraphStyle(
            'CustomFooter',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=10,
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
        
        # Page size: Landscape A4
        page_size = landscape(A4)
        page_width, page_height = page_size
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            rightMargin=48,
            leftMargin=48,
            topMargin=56,
            bottomMargin=56
        )
        
        # Build PDF content
        story = []
        
        # Primary heading band
        title = Paragraph("CERTIFICATE OF COMPLETION", self.title_style)
        story.append(title)
        story.append(Spacer(1, 6))
        
        # Add subtitle
        subtitle = Paragraph("This certifies that", self.subtitle_style)
        story.append(subtitle)
        story.append(Spacer(1, 8))
        
        # Add user name
        name = Paragraph(certificate_data['user_name'], self.name_style)
        story.append(name)
        story.append(Spacer(1, 6))
        
        # Add completion text
        course_name = certificate_data.get('course', 'Cyberaware Program')
        completion_text = Paragraph(
            f"has successfully passed the {course_name} assessment with a score of {certificate_data['score']}%",
            self.content_style
        )
        story.append(completion_text)
        # Declaration line and bold title
        declaration_line = Paragraph("and is hereby declared a", self.content_style)
        story.append(declaration_line)
        declared_title = certificate_data.get('declared_title', 'CyberAwareness Practitioner')
        declared_title_para = Paragraph(declared_title, self.award_title_style)
        story.append(declared_title_para)

        # Space reserved so the center badge placeholder sits right beneath the title
        story.append(Spacer(1, 120))
        
        # Add issue date
        date_text = Paragraph(
            f"Issued on: {certificate_data['issued_date']}",
            self.content_style
        )
        story.append(date_text)
        story.append(Spacer(1, 30))
        
        # Certificate ID intentionally removed as requested
        
        # Build PDF with a custom background and placeholders
        def draw_background(canvas, doc):
            canvas.saveState()
            # Background base
            canvas.setFillColor(self.light_grey)
            canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)

            # Outer border
            canvas.setStrokeColor(self.dark_navy)
            canvas.setLineWidth(3)
            canvas.roundRect(18, 18, page_width - 36, page_height - 36, 12, stroke=1, fill=0)

            # Decorative top-right and bottom-left bands (aligned symmetrically)
            canvas.setFillColor(self.primary_orange)
            band_w = 192
            band_h = 12
            # top-right
            canvas.rect(page_width - 36 - band_w, page_height - 36 - band_h, band_w, band_h, fill=1, stroke=0)
            # bottom-left
            canvas.rect(36, 36, band_w, band_h, fill=1, stroke=0)

            # Thin inner border accent
            canvas.setStrokeColor(self.primary_orange)
            canvas.setLineWidth(1)
            canvas.roundRect(30, 30, page_width - 60, page_height - 60, 10, stroke=1, fill=0)

            # Watermark: use image if available, else draw text watermark
            wm_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'watermark.svg')
            if os.path.exists(wm_path):
                canvas.saveState()
                canvas.translate(page_width/2, page_height/2)
                canvas.rotate(30)
                try:
                    canvas.setFillAlpha(0.08)
                except Exception:
                    pass
                canvas.drawImage(wm_path, -300, -200, width=600, height=400, preserveAspectRatio=True, mask='auto')
                canvas.restoreState()
            else:
                canvas.saveState()
                canvas.setFillColor(colors.Color(0.95, 0.55, 0.20, alpha=0.08))
                canvas.setFont('Helvetica-Bold', 120)
                canvas.translate(page_width/2, page_height/2)
                canvas.rotate(30)
                canvas.drawCentredString(0, 0, 'WATERMARK')
                canvas.restoreState()

            # Center badge image if present; otherwise show placeholder rings
            badge_size = 140
            badge_cx = page_width / 2
            badge_cy = page_height / 2 + 40
            badge_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'badge.svg')
            if os.path.exists(badge_path):
                canvas.drawImage(
                    badge_path,
                    badge_cx - badge_size/2,
                    badge_cy - badge_size/2,
                    width=badge_size,
                    height=badge_size,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            else:
                badge_radius = badge_size / 2
                canvas.saveState()
                canvas.setDash(6, 6)
                canvas.setLineWidth(2)
                canvas.setStrokeColor(self.primary_orange)
                canvas.circle(badge_cx, badge_cy, badge_radius, stroke=1, fill=0)
                # Inner ring
                canvas.setDash(2, 4)
                canvas.setStrokeColor(self.dark_navy)
                canvas.circle(badge_cx, badge_cy, badge_radius - 10, stroke=1, fill=0)
                # Badge label
                canvas.setDash()
                canvas.setFillColor(colors.grey)
                canvas.setFont('Helvetica-Bold', 10)
                canvas.drawCentredString(badge_cx, badge_cy - badge_radius - 14, 'BADGE AREA (140x140)')
                canvas.restoreState()

            # Logo: draw image if available, else dashed placeholder box
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.svg')
            if os.path.exists(logo_path):
                canvas.drawImage(logo_path, 48, page_height - 120, width=120, height=60, preserveAspectRatio=True, mask='auto')
            else:
                canvas.setDash(4, 4)
                canvas.setStrokeColor(colors.grey)
                canvas.rect(48, page_height - 120, 120, 60, fill=0, stroke=1)
                canvas.setFont('Helvetica', 9)
                canvas.setFillColor(colors.grey)
                canvas.drawString(54, page_height - 85, 'LOGO HERE (120x60)')
                canvas.setDash()

            # Signature: draw image if available, else placeholder and line/label
            sig_w = 220
            sig_h = 60
            sig_x = page_width - 48 - sig_w
            sig_y = 72
            signature_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'signature.svg')
            if os.path.exists(signature_path):
                canvas.drawImage(signature_path, sig_x, sig_y, width=sig_w, height=sig_h, preserveAspectRatio=True, mask='auto')
            else:
                canvas.setDash(4, 4)
                canvas.rect(sig_x, sig_y, sig_w, sig_h, fill=0, stroke=1)
                canvas.setDash()
            # Signature line and label (always draw)
            canvas.setStrokeColor(self.dark_navy)
            canvas.line(sig_x, sig_y - 8, sig_x + sig_w, sig_y - 8)
            canvas.setFont('Helvetica', 10)
            canvas.setFillColor(colors.black)
            canvas.drawRightString(sig_x + sig_w, sig_y - 22, 'Authorized Signature')
            canvas.restoreState()

        doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
        
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
        title = Paragraph("CERTIFICATE OF COMPLETION", self.title_style)
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
            f"Congratulations! You have successfully passed the Cyberaware Program assessment with a score of {certificate_data['score']}%",
            self.content_style
        )
        story.append(completion_msg)
        
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content 