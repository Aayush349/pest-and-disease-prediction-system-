from fpdf import FPDF
import qrcode
import os
import socket
from pathlib import Path
from datetime import datetime
from ..config import get_settings

settings = get_settings()
PDF_DIR = Path(settings.UPLOAD_DIR) / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

# Font paths
FONTS_DIR = Path(os.getcwd()) / "backend" / "fonts"

# --- 🎨 COLORS ---
COLOR_BRAND_GREEN = (33, 150, 83)
COLOR_TEXT_BLACK = (20, 20, 20)
COLOR_STATUS_RED = (220, 53, 69)
COLOR_SECTION_GRAY = (240, 242, 245)

FONT_MAP = {
    "hi": "hindi.ttf", 
    "mr": "hindi.ttf", 
    "ta": "tamil.ttf", 
    "te": "telugu.ttf", 
    "kn": "kannada.ttf", 
    "en": "hindi.ttf",
    "en-US": "hindi.ttf"
}

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except: 
        return "localhost"

class AgroHealthPDF(FPDF):
    def header(self):
        # Top Branding Bar
        self.set_fill_color(*COLOR_BRAND_GREEN)
        self.rect(0, 0, 210, 35, 'F')
        self.set_y(10)
        self.set_font('Helvetica', 'B', 22)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'AGROGUARD DIGITAL HEALTH CARD', 0, 1, 'C')
        self.set_font('Helvetica', '', 10)
        self.cell(0, 5, 'AI-Powered Crop Diagnostics & Satellite Insight', 0, 1, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f'This is an AI generated advice. Consult local experts for confirmation. | Page {self.page_no()}', 0, 0, 'C')

def generate_prescription_pdf(data: dict, filename_base: str) -> str:
    """Generate PDF prescription with multilingual support"""
    pdf = AgroHealthPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # --- FONT HANDLING - SIMPLIFIED APPROACH ---
    target_lang = data.get("language", "en")
    font_filename = FONT_MAP.get(target_lang, "hindi.ttf")
    
    # Try to find font file
    font_path = FONTS_DIR / font_filename
    if not font_path.exists():
        # Try other possible locations
        other_paths = [
            Path(".") / "fonts" / font_filename,
            Path("..") / "fonts" / font_filename,
            Path(os.getcwd()) / "fonts" / font_filename,
        ]
        for path in other_paths:
            if path.exists():
                font_path = path
                break
    
    has_unicode_font = False
    unicode_font_name = "UnicodeFont"
    
    if font_path.exists():
        try:
            # Register the Unicode font
            pdf.add_font(unicode_font_name, '', str(font_path), uni=True)
            has_unicode_font = True
            print(f"✓ Loaded Unicode font: {font_path}")
        except Exception as e:
            print(f"⚠ Could not load Unicode font: {e}")
            has_unicode_font = False
    
    # Helper function to safely handle text
    def safe_pdf_text(text):
        """Convert text to safe string for PDF"""
        if not text:
            return ""
        
        # Always return string
        text_str = str(text)
        
        # If we have Unicode font, return as-is
        if has_unicode_font:
            return text_str
        
        # Otherwise, try to keep only ASCII characters
        try:
            return text_str.encode('ascii', 'ignore').decode('ascii')
        except:
            # If that fails, try latin-1
            try:
                return text_str.encode('latin-1', 'ignore').decode('latin-1')
            except:
                return "[Non-ASCII content]"
    
    # Helper to set appropriate font - **FIXED VERSION**
    def set_appropriate_font(is_unicode_content=False, is_bold=False, size=10):
        """Set font for PDF based on whether we need Unicode support"""
        if is_unicode_content and has_unicode_font:
            style = 'B' if is_bold else ''
            pdf.set_font(unicode_font_name, style, size)
        else:
            style = 'B' if is_bold else ''
            pdf.set_font('Helvetica', style, size)
    
    # --- 1. METADATA CARD ---
    pdf.set_fill_color(*COLOR_SECTION_GRAY)
    pdf.rect(10, 40, 190, 35, 'F')
    
    pdf.set_y(42)
    pdf.set_x(15)
    pdf.set_text_color(*COLOR_TEXT_BLACK)
    
    # Row 1: REPORT ID & DATE (English - use Helvetica)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(40, 6, "REPORT ID:", 0, 0)
    pdf.set_font("Helvetica", '', 10)
    safe_id = str(filename_base)[:8].upper() if filename_base else "UNKNOWN"
    pdf.cell(60, 6, f"#{safe_id}", 0, 0)
    
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(30, 6, "DATE:", 0, 0)
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(0, 6, datetime.now().strftime("%d %B, %Y | %H:%M"), 0, 1)
    
    # Row 2: FARMER ID & CROP STAGE (may contain Unicode)
    pdf.set_x(15)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(40, 6, "FARMER ID:", 0, 0)
    
    # Farmer ID value
    farmer_id = data.get('farmer_id', 'Guest')
    set_appropriate_font(is_unicode_content=False, is_bold=False, size=10)
    pdf.cell(60, 6, safe_pdf_text(farmer_id), 0, 0)
    
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(30, 6, "CROP STAGE:", 0, 0)
    
    crop_stage = data.get('crop_stage', 'Vegetative')
    set_appropriate_font(is_unicode_content=False, is_bold=False, size=10)
    pdf.cell(0, 6, safe_pdf_text(crop_stage), 0, 1)
    
    # Row 3: AI MODEL (English)
    pdf.set_x(15)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(50, 6, "AI MODEL:", 0, 0)
    pdf.set_font("Helvetica", '', 10)
    model_used = data.get('model_used', 'Dual-Core YOLO')
    pdf.cell(0, 6, str(model_used), 0, 1)
    
    pdf.ln(5)
    
    # --- 2. DIAGNOSIS SECTION ---
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(*COLOR_STATUS_RED)
    
    raw_disease = data.get("disease", "Unknown")
    disease_display = str(raw_disease).replace("___", " ").replace("_", " ").upper()
    
    # Disease name is from model (should be English)
    pdf.cell(0, 10, f"DETECTED: {disease_display}", 0, 1, 'L')
    
    # Confidence score
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_text_color(*COLOR_TEXT_BLACK)
    try:
        conf = float(data.get('confidence', 0)) * 100
        conf_text = f"Model Confidence Score: {conf:.1f}%"
    except (ValueError, TypeError):
        conf_text = "Model Confidence: N/A"
    
    pdf.cell(0, 6, conf_text, 0, 1, 'L')
    
    # Advisory source
    advisory_source = data.get('advisory_source', '')
    if advisory_source:
        pdf.set_font("Helvetica", 'I', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"Advisory Source: {advisory_source}", 0, 1, 'L')
    
    # Image
    img_path = data.get('image_path')
    if img_path and os.path.exists(img_path):
        pdf.ln(5)
        if pdf.get_y() > 180:
            pdf.add_page()
        
        try:
            x_pos = (210 - 80) / 2
            pdf.image(img_path, x=x_pos, w=80, h=60)
            pdf.ln(5)
        except Exception as e:
            print(f"Image error: {e}")
            pdf.ln(10)
    else:
        pdf.ln(10)
    
    # --- 3. TREATMENT PLAN ---
    if pdf.get_y() > 230:
        pdf.add_page()
    
    pdf.ln(5)
    pdf.set_fill_color(*COLOR_BRAND_GREEN)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 8, "  TREATMENT PLAN", 0, 1, 'L', fill=True)
    pdf.ln(5)
    
    treatments = data.get('treatment', [])
    if not treatments:
        treatments = ["No specific treatment plan available. Please consult an agricultural expert."]
    
    # Set font for treatment steps - CRITICAL FIX
    if has_unicode_font:
        pdf.set_font(unicode_font_name, '', 11)
    else:
        pdf.set_font("Helvetica", '', 11)
    
    pdf.set_text_color(*COLOR_TEXT_BLACK)
    
    for i, step in enumerate(treatments, 1):
        if pdf.get_y() > 250:
            pdf.add_page()
            if has_unicode_font:
                pdf.set_font(unicode_font_name, '', 11)
            else:
                pdf.set_font("Helvetica", '', 11)
        
        safe_step = safe_pdf_text(str(step))
        pdf.multi_cell(0, 7, f"{i}. {safe_step}")
        pdf.ln(2)
    
    # --- 4. PREVENTION PLAN --- **THIS WAS THE BUG**
    if pdf.get_y() > 220:
        pdf.add_page()
    
    pdf.ln(5)
    pdf.set_fill_color(255, 193, 7)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 8, "  PREVENTIVE MEASURES", 0, 1, 'L', fill=True)
    pdf.ln(5)
    
    preventions = data.get('prevention', [])
    if not preventions:
        preventions = ["Ensure field sanitation and consult an agricultural expert."]
    
    # Set font for prevention steps - CRITICAL FIX
    if has_unicode_font:
        pdf.set_font(unicode_font_name, '', 11)
    else:
        pdf.set_font("Helvetica", '', 11)
    
    pdf.set_text_color(*COLOR_TEXT_BLACK)
    
    for i, step in enumerate(preventions, 1):
        if pdf.get_y() > 250:
            pdf.add_page()
            if has_unicode_font:
                pdf.set_font(unicode_font_name, '', 11)
            else:
                pdf.set_font("Helvetica", '', 11)
        
        safe_step = safe_pdf_text(str(step))
        pdf.multi_cell(0, 7, f"{i}. {safe_step}")
        pdf.ln(2)
    
    # --- 5. QR CODE FOR AUDIO ---
    pdf.ln(10)
    y_pos = pdf.get_y()
    
    if y_pos > 200:
        pdf.add_page()
        y_pos = 40
    
    # Generate audio link
    local_ip = get_local_ip()
    audio_url = data.get('audio_url', '')
    
    if audio_url:
        try:
            # Fix URL
            if "localhost" in audio_url:
                audio_url = audio_url.replace("localhost", local_ip)
            elif audio_url.startswith("/uploads/audio"):
                audio_url = f"http://{local_ip}:8000{audio_url}"
            
            # Generate QR
            qr = qrcode.make(audio_url)
            temp_qr = PDF_DIR / f"temp_qr_{filename_base}.png"
            qr.save(temp_qr)
            
            # Draw box
            pdf.set_draw_color(200, 200, 200)
            pdf.set_fill_color(255, 255, 255)
            
            qr_x = 140
            qr_y = y_pos
            qr_width = 50
            qr_height = 55
            
            pdf.rect(qr_x, qr_y, qr_width, qr_height, 'FD')
            
            # Add QR image
            pdf.image(str(temp_qr), x=qr_x + 5, y=qr_y + 5, w=40, h=40)
            
            # Add label
            pdf.set_xy(qr_x, qr_y + 45)
            pdf.set_font("Helvetica", 'B', 9)
            pdf.set_text_color(*COLOR_BRAND_GREEN)
            pdf.cell(qr_width, 5, "SCAN FOR AUDIO ADVICE", 0, 1, 'C')
            
            # Clean up
            if os.path.exists(temp_qr):
                os.remove(temp_qr)
                
        except Exception as e:
            print(f"QR Code error: {e}")
    
    # --- 6. DISCLAIMER ---
    pdf.set_y(-40)
    pdf.set_font("Helvetica", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    
    disclaimer = "Note: This is an AI-generated diagnosis based on image analysis. For critical decisions, please consult with certified agricultural experts."
    pdf.multi_cell(0, 4, disclaimer, 0, 'C')
    
    # --- SAVE PDF ---
    pdf_filename = f"health_card_{filename_base}.pdf"
    output_path = PDF_DIR / pdf_filename
    
    try:
        pdf.output(str(output_path))
        print(f"✓ PDF generated successfully: {output_path}")

        return f"http://{local_ip}:8000/uploads/pdfs/{pdf_filename}"
        
    except Exception as e:
        print(f"✗ PDF generation failed: {e}")
        # Fallback: Generate simple ASCII-only PDF
        return generate_simple_fallback_pdf(data, filename_base)

def generate_simple_fallback_pdf(data: dict, filename_base: str) -> str:
    """Fallback PDF generator - ASCII only"""
    from fpdf import FPDF
    
    pdf = FPDF()
    pdf.add_page()
    
    # Simple header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'AgroGuard Report', 0, 1, 'C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Report ID: {str(filename_base)[:8]}", 0, 1, 'C')
    pdf.ln(10)
    
    # Disease info
    pdf.set_font('Arial', 'B', 14)
    disease = data.get('disease', 'Unknown')
    disease_clean = str(disease).replace('_', ' ').replace('___', ' ')
    pdf.cell(0, 10, f'Disease: {disease_clean}', 0, 1)
    
    # Confidence
    pdf.set_font('Arial', '', 12)
    try:
        conf = float(data.get('confidence', 0)) * 100
        pdf.cell(0, 10, f'Confidence: {conf:.1f}%', 0, 1)
    except:
        pass
    
    pdf.ln(5)
    
    # Treatment
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Treatment:', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    treatments = data.get('treatment', [])
    if not treatments:
        treatments = ["Consult an agricultural expert."]
    
    for i, step in enumerate(treatments, 1):
        # Convert to ASCII only
        try:
            step_clean = str(step).encode('ascii', 'ignore').decode('ascii')
        except:
            step_clean = str(step)
        pdf.multi_cell(0, 5, f"{i}. {step_clean}")
    
    # Prevention
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Prevention:', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    preventions = data.get('prevention', [])
    if not preventions:
        preventions = ["Ensure field sanitation."]
    
    for i, step in enumerate(preventions, 1):
        # Convert to ASCII only
        try:
            step_clean = str(step).encode('ascii', 'ignore').decode('ascii')
        except:
            step_clean = str(step)
        pdf.multi_cell(0, 5, f"{i}. {step_clean}")
    
    # Footer
    pdf.set_y(-15)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, 'Generated by AgroGuard AI System', 0, 0, 'C')
    
    # Save
    pdf_filename = f"simple_report_{filename_base}.pdf"
    output_path = PDF_DIR / pdf_filename
    
    try:
        pdf.output(str(output_path))
        local_ip = get_local_ip()
        return f"http://{local_ip}:8000/uploads/pdfs/{pdf_filename}"
    except Exception as e:
        print(f"Even simple PDF failed: {e}")
        return ""




# from fpdf import FPDF
# import qrcode
# import os
# import socket
# from pathlib import Path
# from datetime import datetime
# from ..config import get_settings

# settings = get_settings()
# UPLOAD_DIR = Path(settings.UPLOAD_DIR)

# # Font paths
# FONTS_DIR = Path(os.getcwd()) / "backend" / "fonts"

# # --- 🎨 COLORS ---
# COLOR_BRAND_GREEN = (33, 150, 83)
# COLOR_TEXT_BLACK = (20, 20, 20)
# COLOR_STATUS_RED = (220, 53, 69)
# COLOR_SECTION_GRAY = (240, 242, 245)

# FONT_MAP = {
#     "hi": "hindi.ttf", 
#     "mr": "hindi.ttf", 
#     "ta": "tamil.ttf", 
#     "te": "telugu.ttf", 
#     "kn": "kannada.ttf", 
#     "en": "hindi.ttf",
#     "en-US": "hindi.ttf"
# }

# def get_local_ip():
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(("8.8.8.8", 80))
#         ip = s.getsockname()[0]
#         s.close()
#         return ip
#     except: 
#         return "localhost"

# class AgroHealthPDF(FPDF):
#     def header(self):
#         # Top Branding Bar
#         self.set_fill_color(*COLOR_BRAND_GREEN)
#         self.rect(0, 0, 210, 35, 'F')
#         self.set_y(10)
#         self.set_font('Helvetica', 'B', 22)
#         self.set_text_color(255, 255, 255)
#         self.cell(0, 10, 'AGROGUARD DIGITAL HEALTH CARD', 0, 1, 'C')
#         self.set_font('Helvetica', '', 10)
#         self.cell(0, 5, 'AI-Powered Crop Diagnostics & Satellite Insight', 0, 1, 'C')
#         self.ln(20)

#     def footer(self):
#         self.set_y(-15)
#         self.set_font('Helvetica', 'I', 8)
#         self.set_text_color(120, 120, 120)
#         self.cell(0, 10, f'This is an AI generated advice. Consult local experts for confirmation. | Page {self.page_no()}', 0, 0, 'C')

# def generate_prescription_pdf(data: dict, filename_base: str) -> str:
#     """Generate PDF prescription with multilingual support"""
#     pdf = AgroHealthPDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=20)
    
#     # --- FONT HANDLING - SIMPLIFIED APPROACH ---
#     target_lang = data.get("language", "en")
#     font_filename = FONT_MAP.get(target_lang, "hindi.ttf")
    
#     # Try to find font file
#     font_path = FONTS_DIR / font_filename
#     if not font_path.exists():
#         # Try other possible locations
#         other_paths = [
#             Path(".") / "fonts" / font_filename,
#             Path("..") / "fonts" / font_filename,
#             Path(os.getcwd()) / "fonts" / font_filename,
#         ]
#         for path in other_paths:
#             if path.exists():
#                 font_path = path
#                 break
    
#     has_unicode_font = False
#     if font_path.exists():
#         try:
#             # Use 'DejaVu' as font family name (fpdf recognizes this as built-in Unicode font)
#             # Or use a custom name
#             font_family = "UnicodeFont"
#             pdf.add_font(font_family, '', str(font_path), uni=True)
#             has_unicode_font = True
#             print(f"✓ Loaded Unicode font: {font_path}")
#         except Exception as e:
#             print(f"⚠ Could not load Unicode font: {e}")
#             has_unicode_font = False
    
#     # Helper function to set appropriate font
#     def set_pdf_font(pdf_obj, is_unicode=False, is_bold=False, size=10):
#         """Set font for PDF based on whether we need Unicode support"""
#         if is_unicode and has_unicode_font:
#             style = 'B' if is_bold else ''
#             pdf_obj.set_font("UnicodeFont", style, size)
#         else:
#             style = 'B' if is_bold else ''
#             pdf_obj.set_font('Helvetica', style, size)
    
#     # Helper to safely handle text
#     def safe_pdf_text(text):
#         """Convert text to safe string for PDF"""
#         if not text:
#             return ""
        
#         # Always return string
#         text_str = str(text)
        
#         # If we have Unicode font, return as-is
#         if has_unicode_font:
#             return text_str
        
#         # Otherwise, try to keep only ASCII characters
#         try:
#             return text_str.encode('ascii', 'ignore').decode('ascii')
#         except:
#             # If that fails, try latin-1
#             try:
#                 return text_str.encode('latin-1', 'ignore').decode('latin-1')
#             except:
#                 return "[Non-ASCII content]"
    
#     # --- 1. METADATA CARD ---
#     pdf.set_fill_color(*COLOR_SECTION_GRAY)
#     pdf.rect(10, 40, 190, 35, 'F')
    
#     pdf.set_y(42)
#     pdf.set_x(15)
#     pdf.set_text_color(*COLOR_TEXT_BLACK)
    
#     # Row 1: REPORT ID & DATE (English - use Helvetica)
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(40, 6, "REPORT ID:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     safe_id = str(filename_base)[:8].upper() if filename_base else "UNKNOWN"
#     pdf.cell(60, 6, f"#{safe_id}", 0, 0)
    
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(30, 6, "DATE:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     pdf.cell(0, 6, datetime.now().strftime("%d %B, %Y | %H:%M"), 0, 1)
    
#     # Row 2: FARMER ID & CROP STAGE (may contain Unicode)
#     pdf.set_x(15)
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(40, 6, "FARMER ID:", 0, 0)
    
#     # Farmer ID value (use Unicode font if needed)
#     farmer_id = data.get('farmer_id', 'Guest')
#     is_farmer_unicode = any(ord(c) > 127 for c in str(farmer_id))
#     set_pdf_font(pdf, is_unicode=is_farmer_unicode, is_bold=False, size=10)
#     pdf.cell(60, 6, safe_pdf_text(farmer_id), 0, 0)
    
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(30, 6, "CROP STAGE:", 0, 0)
    
#     crop_stage = data.get('crop_stage', 'Vegetative')
#     is_crop_unicode = any(ord(c) > 127 for c in str(crop_stage))
#     set_pdf_font(pdf, is_unicode=is_crop_unicode, is_bold=False, size=10)
#     pdf.cell(0, 6, safe_pdf_text(crop_stage), 0, 1)
    
#     # Row 3: AI MODEL (English)
#     pdf.set_x(15)
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(50, 6, "AI MODEL:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     model_used = data.get('model_used', 'Dual-Core YOLO')
#     pdf.cell(0, 6, str(model_used), 0, 1)
    
#     pdf.ln(5)
    
#     # --- 2. DIAGNOSIS SECTION ---
#     pdf.set_font("Helvetica", 'B', 18)
#     pdf.set_text_color(*COLOR_STATUS_RED)
    
#     raw_disease = data.get("disease", "Unknown")
#     disease_display = str(raw_disease).replace("___", " ").replace("_", " ").upper()
    
#     # Disease name is from model (should be English)
#     pdf.cell(0, 10, f"DETECTED: {disease_display}", 0, 1, 'L')
    
#     # Confidence score
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.set_text_color(*COLOR_TEXT_BLACK)
#     try:
#         conf = float(data.get('confidence', 0)) * 100
#         conf_text = f"Model Confidence Score: {conf:.1f}%"
#     except (ValueError, TypeError):
#         conf_text = "Model Confidence: N/A"
    
#     pdf.cell(0, 6, conf_text, 0, 1, 'L')
    
#     # Advisory source
#     advisory_source = data.get('advisory_source', '')
#     if advisory_source:
#         pdf.set_font("Helvetica", 'I', 9)
#         pdf.set_text_color(100, 100, 100)
#         pdf.cell(0, 5, f"Advisory Source: {advisory_source}", 0, 1, 'L')
    
#     # Image
#     img_path = data.get('image_path')
#     if img_path and os.path.exists(img_path):
#         pdf.ln(5)
#         if pdf.get_y() > 180:
#             pdf.add_page()
        
#         try:
#             x_pos = (210 - 80) / 2
#             pdf.image(img_path, x=x_pos, w=80, h=60)
#             pdf.ln(5)
#         except Exception as e:
#             print(f"Image error: {e}")
#             pdf.ln(10)
#     else:
#         pdf.ln(10)
    
#     # --- 3. TREATMENT PLAN ---
#     if pdf.get_y() > 230:
#         pdf.add_page()
    
#     pdf.ln(5)
#     pdf.set_fill_color(*COLOR_BRAND_GREEN)
#     pdf.set_text_color(255, 255, 255)
#     pdf.set_font("Helvetica", 'B', 12)
#     pdf.cell(190, 8, "  TREATMENT PLAN", 0, 1, 'L', fill=True)
#     pdf.ln(5)
    
#     treatments = data.get('treatment', [])
#     if not treatments:
#         treatments = ["No specific treatment plan available. Please consult an agricultural expert."]
    
#     # Check if any treatment step has Unicode characters
#     has_unicode_treatments = any(any(ord(c) > 127 for c in str(step)) for step in treatments)
    
#     for i, step in enumerate(treatments, 1):
#         if pdf.get_y() > 250:
#             pdf.add_page()
        
#         # Set font based on content
#         step_str = str(step)
#         step_has_unicode = any(ord(c) > 127 for c in step_str)
#         set_pdf_font(pdf, is_unicode=step_has_unicode or has_unicode_treatments, is_bold=False, size=11)
        
#         # Use safe text
#         safe_step = safe_pdf_text(step_str)
#         pdf.multi_cell(0, 7, f"{i}. {safe_step}")
#         pdf.ln(2)
    
#     # --- 4. PREVENTION PLAN ---
#     if pdf.get_y() > 220:
#         pdf.add_page()
    
#     pdf.ln(5)
#     pdf.set_fill_color(255, 193, 7)
#     pdf.set_text_color(0, 0, 0)
#     pdf.set_font("Helvetica", 'B', 12)
#     pdf.cell(190, 8, "  PREVENTIVE MEASURES", 0, 1, 'L', fill=True)
#     pdf.ln(5)
    
#     preventions = data.get('prevention', [])
#     if not preventions:
#         preventions = ["Ensure field sanitation and consult an agricultural expert."]
    
#     # Check if any prevention step has Unicode characters
#     has_unicode_preventions = any(any(ord(c) > 127 for c in str(step)) for step in preventions)
    
#     for i, step in enumerate(preventions, 1):
#         if pdf.get_y() > 250:
#             pdf.add_page()
        
#         # Set font based on content
#         step_str = str(step)
#         step_has_unicode = any(ord(c) > 127 for c in step_str)
#         set_pdf_font(pdf, is_unicode=step_has_unicode or has_unicode_preventions, is_bold=False, size=11)
        
#         # Use safe text
#         safe_step = safe_pdf_text(step_str)
#         pdf.multi_cell(0, 7, f"{i}. {safe_step}")
#         pdf.ln(2)
    
#     # --- 5. QR CODE FOR AUDIO ---
#     pdf.ln(10)
#     y_pos = pdf.get_y()
    
#     if y_pos > 200:
#         pdf.add_page()
#         y_pos = 40
    
#     # Generate audio link
#     local_ip = get_local_ip()
#     audio_url = data.get('audio_url', '')
    
#     if audio_url:
#         try:
#             # Fix URL
#             if "localhost" in audio_url:
#                 audio_url = audio_url.replace("localhost", local_ip)
#             elif audio_url.startswith("/uploads/"):
#                 audio_url = f"http://{local_ip}:8000{audio_url}"
            
#             # Generate QR
#             qr = qrcode.make(audio_url)
#             temp_qr = UPLOAD_DIR / f"temp_qr_{filename_base}.png"
#             qr.save(temp_qr)
            
#             # Draw box
#             pdf.set_draw_color(200, 200, 200)
#             pdf.set_fill_color(255, 255, 255)
            
#             qr_x = 140
#             qr_y = y_pos
#             qr_width = 50
#             qr_height = 55
            
#             pdf.rect(qr_x, qr_y, qr_width, qr_height, 'FD')
            
#             # Add QR image
#             pdf.image(str(temp_qr), x=qr_x + 5, y=qr_y + 5, w=40, h=40)
            
#             # Add label
#             pdf.set_xy(qr_x, qr_y + 45)
#             pdf.set_font("Helvetica", 'B', 9)
#             pdf.set_text_color(*COLOR_BRAND_GREEN)
#             pdf.cell(qr_width, 5, "SCAN FOR AUDIO ADVICE", 0, 1, 'C')
            
#             # Clean up
#             if os.path.exists(temp_qr):
#                 os.remove(temp_qr)
                
#         except Exception as e:
#             print(f"QR Code error: {e}")
    
#     # --- 6. DISCLAIMER ---
#     pdf.set_y(-40)
#     pdf.set_font("Helvetica", 'I', 8)
#     pdf.set_text_color(150, 150, 150)
    
#     disclaimer = "Note: This is an AI-generated diagnosis based on image analysis. For critical decisions, please consult with certified agricultural experts."
#     pdf.multi_cell(0, 4, disclaimer, 0, 'C')
    
#     # --- SAVE PDF ---
#     pdf_filename = f"health_card_{filename_base}.pdf"
#     output_path = UPLOAD_DIR / pdf_filename
    
#     try:
#         pdf.output(str(output_path))
#         print(f"✓ PDF generated successfully: {output_path}")
        
#         return f"http://{local_ip}:8000/uploads/{pdf_filename}"
        
#     except Exception as e:
#         print(f"✗ PDF generation failed: {e}")
#         # Fallback: Generate simple ASCII-only PDF
#         return generate_simple_fallback_pdf(data, filename_base)

# def generate_simple_fallback_pdf(data: dict, filename_base: str) -> str:
#     """Fallback PDF generator - ASCII only"""
#     from fpdf import FPDF
    
#     pdf = FPDF()
#     pdf.add_page()
    
#     # Simple header
#     pdf.set_font('Arial', 'B', 16)
#     pdf.cell(0, 10, 'AgroGuard Report', 0, 1, 'C')
#     pdf.set_font('Arial', '', 12)
#     pdf.cell(0, 10, f"Report ID: {str(filename_base)[:8]}", 0, 1, 'C')
#     pdf.ln(10)
    
#     # Disease info
#     pdf.set_font('Arial', 'B', 14)
#     disease = data.get('disease', 'Unknown')
#     disease_clean = str(disease).replace('_', ' ').replace('___', ' ')
#     pdf.cell(0, 10, f'Disease: {disease_clean}', 0, 1)
    
#     # Confidence
#     pdf.set_font('Arial', '', 12)
#     try:
#         conf = float(data.get('confidence', 0)) * 100
#         pdf.cell(0, 10, f'Confidence: {conf:.1f}%', 0, 1)
#     except:
#         pass
    
#     pdf.ln(5)
    
#     # Treatment
#     pdf.set_font('Arial', 'B', 12)
#     pdf.cell(0, 10, 'Treatment:', 0, 1)
#     pdf.set_font('Arial', '', 10)
    
#     treatments = data.get('treatment', [])
#     if not treatments:
#         treatments = ["Consult an agricultural expert."]
    
#     for i, step in enumerate(treatments, 1):
#         # Convert to ASCII only
#         try:
#             step_clean = str(step).encode('ascii', 'ignore').decode('ascii')
#         except:
#             step_clean = str(step)
#         pdf.multi_cell(0, 5, f"{i}. {step_clean}")
    
#     # Prevention
#     pdf.ln(5)
#     pdf.set_font('Arial', 'B', 12)
#     pdf.cell(0, 10, 'Prevention:', 0, 1)
#     pdf.set_font('Arial', '', 10)
    
#     preventions = data.get('prevention', [])
#     if not preventions:
#         preventions = ["Ensure field sanitation."]
    
#     for i, step in enumerate(preventions, 1):
#         # Convert to ASCII only
#         try:
#             step_clean = str(step).encode('ascii', 'ignore').decode('ascii')
#         except:
#             step_clean = str(step)
#         pdf.multi_cell(0, 5, f"{i}. {step_clean}")
    
#     # Footer
#     pdf.set_y(-15)
#     pdf.set_font('Arial', 'I', 8)
#     pdf.cell(0, 10, 'Generated by AgroGuard AI System', 0, 0, 'C')
    
#     # Save
#     pdf_filename = f"simple_report_{filename_base}.pdf"
#     output_path = UPLOAD_DIR / pdf_filename
    
#     try:
#         pdf.output(str(output_path))
#         local_ip = get_local_ip()
#         return f"http://{local_ip}:8000/uploads/{pdf_filename}"
#     except Exception as e:
#         print(f"Even simple PDF failed: {e}")
#         return ""




# from fpdf import FPDF
# import qrcode
# import os
# import socket
# from pathlib import Path
# from datetime import datetime
# from ..config import get_settings

# settings = get_settings()
# UPLOAD_DIR = Path(settings.UPLOAD_DIR)
# # Path fix based on your folder structure
# FONTS_DIR = Path(os.getcwd()) / "backend" / "fonts" 

# # --- 🎨 ENTERPRISE BRANDING ---
# COLOR_BRAND_GREEN = (33, 150, 83)
# COLOR_TEXT_BLACK = (20, 20, 20)
# COLOR_STATUS_RED = (220, 53, 69)
# COLOR_SECTION_GRAY = (240, 242, 245)
# COLOR_BRAND_BG = (33, 150, 83)      # AgroGuard Green (old)
# COLOR_BRAND_TEXT = (255, 255, 255)  # White (old)
# COLOR_SECTION_BG = (245, 247, 250)  # Light Gray (old)
# COLOR_TEXT_MAIN = (45, 55, 72)      # Dark Slate (old)
# COLOR_DANGER = (220, 53, 69)        # Red (old)
# COLOR_ACCENT = (50, 50, 50)         # (old)

# FONT_MAP = {
#     "hi": "hindi.ttf", "mr": "hindi.ttf", "ta": "tamil.ttf", 
#     "te": "telugu.ttf", "kn": "kannada.ttf", "en": "hindi.ttf"
# }

# def get_local_ip():
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(("8.8.8.8", 80))
#         ip = s.getsockname()[0]
#         s.close()
#         return ip
#     except: 
#         return "localhost"

# class AgroHealthPDF(FPDF):
#     def header(self):
#         # Top Branding Bar - Better design
#         self.set_fill_color(*COLOR_BRAND_GREEN)
#         self.rect(0, 0, 210, 35, 'F')
#         self.set_y(10)
        
#         # Main title
#         self.set_font('Helvetica', 'B', 22)
#         self.set_text_color(255, 255, 255)
#         self.cell(0, 10, 'AGROGUARD DIGITAL HEALTH CARD', 0, 1, 'C')
        
#         # Subtitle
#         self.set_font('Helvetica', '', 10)
#         self.cell(0, 5, 'AI-Powered Crop Diagnostics & Satellite Insight', 0, 1, 'C')
        
#         # Add logo if available
#         logo_path = Path(os.getcwd()) / "backend" / "static" / "logo.png"
#         if logo_path.exists():
#             self.image(str(logo_path), x=180, y=5, w=20, h=20)
        
#         self.ln(20)

#     def footer(self):
#         self.set_y(-15)
#         self.set_font('Helvetica', 'I', 8)
#         self.set_text_color(120, 120, 120)
#         self.cell(0, 10, f'This is an AI generated advice. Consult local experts for confirmation. | Page {self.page_no()}', 0, 0, 'C')
#         self.cell(0, 10, f'Generated on {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'R')

# def generate_prescription_pdf(data: dict, filename_base: str) -> str:
#     # Initialize PDF with new design
#     pdf = AgroHealthPDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=20)
    
#     # --- DYNAMIC FONT LOADING (from old code) ---
#     target_lang = data.get("language", "en")
#     font_filename = FONT_MAP.get(target_lang, "hindi.ttf")
    
#     # Font Path Fix: Check multiple locations
#     font_path = FONTS_DIR / font_filename
#     if not font_path.exists():
#         # Try alternative paths
#         alt_paths = [
#             Path(os.getcwd()) / "fonts" / font_filename,
#             Path(os.getcwd()) / "backend" / "fonts" / font_filename,
#             Path(".") / "fonts" / font_filename,
#         ]
#         for alt_path in alt_paths:
#             if alt_path.exists():
#                 font_path = alt_path
#                 break
    
#     has_unicode_font = False
#     if font_path.exists():
#         try:
#             pdf.add_font('LocalFont', '', str(font_path), uni=True)
#             has_unicode_font = True
#         except Exception as e:
#             print(f"Font Error: {e}")
#             has_unicode_font = False
#     else:
#         print(f"Font file not found: {font_filename}")
#         has_unicode_font = False
    
#     def clean_text(text):
#         """Clean text for PDF rendering (from old code)"""
#         if not has_unicode_font and isinstance(text, str):
#             # Try to encode as latin-1 for compatibility
#             try:
#                 return text.encode('latin-1', 'ignore').decode('latin-1')
#             except:
#                 return str(text)
#         return text
    
#     # --- 1. METADATA CARD (Combined from old and new) ---
#     pdf.set_fill_color(*COLOR_SECTION_GRAY)
#     pdf.rect(10, 40, 190, 35, 'F')
    
#     pdf.set_y(42)
#     pdf.set_x(15)
#     pdf.set_text_color(*COLOR_TEXT_BLACK)
    
#     # Row 1: REPORT ID & DATE (Improved from old code)
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(40, 6, "REPORT ID:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
    
#     # Safe ID handling (from old code)
#     safe_id = filename_base
#     if not isinstance(safe_id, str):
#         safe_id = str(safe_id)
#     safe_id = safe_id[:8].upper()
#     pdf.cell(60, 6, f"#{safe_id}", 0, 0)
    
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(30, 6, "DATE:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     pdf.cell(0, 6, datetime.now().strftime("%d %B, %Y | %H:%M"), 0, 1)
    
#     # Row 2: FARMER ID & CROP STAGE (from old code, improved)
#     pdf.set_x(15)
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(40, 6, "FARMER ID:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     farmer_id = data.get('farmer_id', 'Guest')
#     pdf.cell(60, 6, str(farmer_id), 0, 0)
    
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(30, 6, "CROP STAGE:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     crop_stage = data.get('crop_stage', 'Vegetative')
#     pdf.cell(0, 6, str(crop_stage), 0, 1)
    
#     # Row 3: KNOWLEDGE SOURCE & ADVISORY SOURCE (new)
#     pdf.set_x(15)
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(50, 6, "AI MODEL:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     model_used = data.get('model_used', 'Dual-Core YOLO')
#     pdf.cell(0, 6, str(model_used), 0, 1)
    
#     pdf.ln(5)
    
#     # --- 2. SATELLITE INSIGHT SECTION (from new code - Optional) ---
#     # Check if satellite data is available
#     ndvi_val = data.get('ndvi_score')
#     health_status = data.get('field_health')
    
#     if ndvi_val or health_status:
#         pdf.set_fill_color(232, 245, 233)  # Very light green
#         pdf.rect(10, pdf.get_y(), 190, 15, 'F')
#         pdf.set_y(pdf.get_y() + 3)
#         pdf.set_x(15)
        
#         pdf.set_font('Helvetica', 'B', 11)
#         pdf.set_text_color(*COLOR_BRAND_GREEN)
        
#         satellite_text = ""
#         if ndvi_val:
#             satellite_text += f"SATELLITE HEALTH (NDVI): {ndvi_val} "
#         if health_status:
#             satellite_text += f" | FIELD STATUS: {health_status.upper()}"
        
#         pdf.cell(0, 8, satellite_text, 0, 1)
#         pdf.ln(5)
    
#     # --- 3. PRIMARY DIAGNOSIS (Combined from both) ---
#     pdf.set_font("Helvetica", 'B', 18)
#     pdf.set_text_color(*COLOR_STATUS_RED)
    
#     # Safe disease name extraction (from old code)
#     raw_disease = data.get("disease", "Unknown")
#     if not isinstance(raw_disease, str):
#         raw_disease = str(raw_disease)
    
#     disease_display = raw_disease.replace("___", " ").replace("_", " ").upper()
#     pdf.cell(0, 10, f"DETECTED: {disease_display}", 0, 1, 'L')
    
#     # Confidence score (from old code, with error handling)
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.set_text_color(*COLOR_ACCENT)
#     try:
#         conf = float(data.get('confidence', 0)) * 100
#         conf_text = f"Model Confidence Score: {conf:.1f}%"
#     except (ValueError, TypeError):
#         conf_text = "Model Confidence: N/A"
    
#     pdf.cell(0, 6, conf_text, 0, 1, 'L')
    
#     # Add advisory source if available
#     advisory_source = data.get('advisory_source', '')
#     if advisory_source:
#         pdf.set_font("Helvetica", 'I', 9)
#         pdf.set_text_color(100, 100, 100)
#         pdf.cell(0, 5, f"Advisory Source: {advisory_source}", 0, 1, 'L')
    
#     # Image placement (from old code with improved positioning)
#     img_path = data.get('image_path')
#     if img_path and os.path.exists(img_path):
#         pdf.ln(5)
        
#         # Check if we have enough space for image
#         if pdf.get_y() > 180:
#             pdf.add_page()
        
#         try:
#             # Center the image
#             x_pos = (210 - 80) / 2  # Center 80mm wide image
#             pdf.image(img_path, x=x_pos, w=80, h=60)
#             pdf.ln(5)
#         except Exception as e:
#             print(f"Error loading image: {e}")
#             pdf.ln(10)
#     else:
#         pdf.ln(10)
    
#     # --- 4. DESCRIPTION SECTION (if available) ---
#     description = data.get('description', '')
#     if description:
#         if pdf.get_y() > 200:
#             pdf.add_page()
        
#         pdf.set_fill_color(240, 248, 255)  # Light blue
#         pdf.set_text_color(30, 30, 30)
#         pdf.set_font("Helvetica", 'B', 12)
#         pdf.cell(190, 8, "  DISEASE DESCRIPTION", 0, 1, 'L', fill=True)
#         pdf.ln(3)
        
#         if has_unicode_font:
#             pdf.set_font("LocalFont", size=10)
#         else:
#             pdf.set_font("Helvetica", '', 10)
        
#         cleaned_desc = clean_text(description)
#         pdf.multi_cell(0, 6, cleaned_desc)
#         pdf.ln(5)
    
#     # --- 5. TREATMENT PLAN (from old code with improvements) ---
#     if pdf.get_y() > 230:
#         pdf.add_page()
    
#     pdf.ln(5)
#     pdf.set_fill_color(*COLOR_BRAND_GREEN)
#     pdf.set_text_color(255, 255, 255)
#     pdf.set_font("Helvetica", 'B', 12)
#     pdf.cell(190, 8, "  TREATMENT PLAN", 0, 1, 'L', fill=True)
#     pdf.ln(5)
    
#     if has_unicode_font:
#         pdf.set_font("LocalFont", size=11)
#     else:
#         pdf.set_font("Helvetica", '', 11)
    
#     pdf.set_text_color(*COLOR_TEXT_MAIN)
#     treatments = data.get('treatment', [])
    
#     if not treatments:
#         treatments = ["No specific treatment plan available. Please consult an agricultural expert."]
    
#     for i, step in enumerate(treatments, 1):
#         step = clean_text(str(step))
#         # Check page break
#         if pdf.get_y() > 250:
#             pdf.add_page()
#             if has_unicode_font:
#                 pdf.set_font("LocalFont", size=11)
#             else:
#                 pdf.set_font("Helvetica", '', 11)
        
#         pdf.multi_cell(0, 7, f"{i}. {step}")
#         pdf.ln(2)
    
#     # --- 6. PREVENTION PLAN (from old code with improvements) ---
#     if pdf.get_y() > 220:
#         pdf.add_page()
    
#     pdf.ln(5)
#     pdf.set_fill_color(255, 193, 7)  # Amber (from old code)
#     pdf.set_text_color(0, 0, 0)
#     pdf.set_font("Helvetica", 'B', 12)
#     pdf.cell(190, 8, "  PREVENTIVE MEASURES", 0, 1, 'L', fill=True)
#     pdf.ln(5)
    
#     if has_unicode_font:
#         pdf.set_font("LocalFont", size=11)
#     else:
#         pdf.set_font("Helvetica", '', 11)
    
#     pdf.set_text_color(*COLOR_TEXT_MAIN)
#     preventions = data.get('prevention', [])
    
#     if not preventions:
#         preventions = ["Ensure field sanitation and consult an agricultural expert."]
    
#     for i, step in enumerate(preventions, 1):
#         step = clean_text(str(step))
#         # Check page break
#         if pdf.get_y() > 250:
#             pdf.add_page()
#             if has_unicode_font:
#                 pdf.set_font("LocalFont", size=11)
#             else:
#                 pdf.set_font("Helvetica", '', 11)
        
#         pdf.multi_cell(0, 7, f"{i}. {step}")
#         pdf.ln(2)
    
#     # --- 7. ADDITIONAL INFORMATION ---
#     knowledge_source = data.get('knowledge_source', '')
#     if knowledge_source:
#         if pdf.get_y() > 250:
#             pdf.add_page()
        
#         pdf.ln(5)
#         pdf.set_font("Helvetica", 'I', 9)
#         pdf.set_text_color(100, 100, 100)
#         pdf.cell(0, 5, f"Knowledge Source: {knowledge_source}", 0, 1)
    
#     # --- 8. QR CODE FOR AUDIO (Combined from both with improvements) ---
#     pdf.ln(10)
#     y_pos = pdf.get_y()
    
#     # CRITICAL: Check if we're too close to bottom
#     if y_pos > 200:
#         pdf.add_page()
#         y_pos = 40  # Below header
    
#     # Generate audio link
#     local_ip = get_local_ip()
#     audio_url = data.get('audio_url', '')
    
#     if audio_url:
#         # Fix localhost in URL
#         if "localhost" in audio_url:
#             audio_url = audio_url.replace("localhost", local_ip)
#         elif audio_url.startswith("/uploads/"):
#             audio_url = f"http://{local_ip}:8000{audio_url}"
        
#         # Generate QR code
#         try:
#             qr = qrcode.make(audio_url)
#             temp_qr = UPLOAD_DIR / f"temp_qr_{filename_base}.png"
#             qr.save(temp_qr)
            
#             # Draw QR box (from old code with improved styling)
#             pdf.set_draw_color(200, 200, 200)
#             pdf.set_fill_color(255, 255, 255)
            
#             # Position at right side
#             qr_x = 140
#             qr_y = y_pos
#             qr_width = 50
#             qr_height = 55
            
#             pdf.rect(qr_x, qr_y, qr_width, qr_height, 'FD')
            
#             # Add QR code image
#             pdf.image(str(temp_qr), x=qr_x + 5, y=qr_y + 5, w=40, h=40)
            
#             # Add label
#             pdf.set_xy(qr_x, qr_y + 45)
#             pdf.set_font("Helvetica", 'B', 9)
#             pdf.set_text_color(*COLOR_BRAND_GREEN)
#             pdf.cell(qr_width, 5, "SCAN FOR AUDIO ADVICE", 0, 1, 'C')
            
#             # Add audio availability note
#             pdf.set_xy(10, qr_y + 10)
#             pdf.set_font("Helvetica", 'I', 9)
#             pdf.set_text_color(100, 100, 100)
#             pdf.multi_cell(120, 5, "Audio advice is available for this diagnosis. Scan the QR code with your phone to listen to treatment instructions in your preferred language.")
            
#             # Clean up temp file
#             if os.path.exists(temp_qr):
#                 os.remove(temp_qr)
                
#         except Exception as e:
#             print(f"QR Code generation failed: {e}")
    
#     # --- 9. DISCLAIMER ---
#     pdf.set_y(-40)
#     pdf.set_font("Helvetica", 'I', 8)
#     pdf.set_text_color(150, 150, 150)
    
#     disclaimer = "Note: This is an AI-generated diagnosis based on image analysis. For critical decisions, please consult with certified agricultural experts and validate recommendations with local conditions."
#     pdf.multi_cell(0, 4, disclaimer, 0, 'C')
    
#     # --- SAVE PDF ---
#     pdf_filename = f"health_card_{filename_base}.pdf"
#     output_path = UPLOAD_DIR / pdf_filename
    
#     try:
#         pdf.output(str(output_path))
#         print(f"✓ PDF saved: {output_path}")
        
#         # Return URL
#         local_ip = get_local_ip()
#         return f"http://{local_ip}:8000/uploads/{pdf_filename}"
        
#     except Exception as e:
#         print(f"✗ PDF generation failed: {e}")
#         # Fallback to old naming if needed
#         pdf_filename = f"report_{filename_base}.pdf"
#         output_path = UPLOAD_DIR / pdf_filename
#         pdf.output(str(output_path))
#         return f"http://{local_ip}:8000/uploads/{pdf_filename}"

# from fpdf import FPDF
# import qrcode
# import os
# import socket
# from pathlib import Path
# from datetime import datetime
# from ..config import get_settings


# settings = get_settings()
# UPLOAD_DIR = Path(settings.UPLOAD_DIR)
# FONTS_DIR = Path(os.getcwd()) / "backend" / "fonts" # ✅ Fixed Path



# # --- 🎨 PROFESSIONAL COLORS ---
# COLOR_BRAND_BG = (33, 150, 83)      # AgroGuard Green
# COLOR_BRAND_TEXT = (255, 255, 255)  # White
# COLOR_SECTION_BG = (245, 247, 250)  # Light Gray
# COLOR_TEXT_MAIN = (45, 55, 72)      # Dark Slate
# COLOR_DANGER = (220, 53, 69)        # Red
# COLOR_ACCENT = (50, 50, 50)

# # --- 🌐 FONT MAPPING ---
# FONT_MAP = {
#     "hi": "hindi.ttf",
#     "mr": "hindi.ttf",
#     "ta": "tamil.ttf",
#     "te": "telugu.ttf",
#     "kn": "kannada.ttf",
#     "en": "hindi.ttf" # Fallback to Hindi font for English to support mixed text
# }

# def get_local_ip():
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(("8.8.8.8", 80))
#         ip = s.getsockname()[0]
#         s.close()
#         return ip
#     except:
#         return "localhost"

# class InternationalPDF(FPDF):
#     def header(self):
#         # Header Height = 40
#         self.set_fill_color(*COLOR_BRAND_BG)
#         self.rect(0, 0, 210, 40, 'F')
#         self.set_y(15)
#         self.set_font('LocalFont', 20)
#         self.set_text_color(*COLOR_BRAND_TEXT)
#         self.cell(0, 10, 'AgroGuard AI', 0, 1, 'C')
#         self.set_font('LocalFont', '', 10)
#         self.cell(0, 5, 'Advanced Plant Disease Analysis Report', 0, 1, 'C')
#         self.ln(25) # Cursor move niche

#     def footer(self):
#         self.set_y(-20)
#         # self.set_font('Helvetica', 'I', 8)
#         self.set_font('LocalFont', 'I', 8)
#         self.set_text_color(150, 150, 150)
#         self.cell(0, 10, f'Generated by AgroGuard System | Page {self.page_no()}', 0, 0, 'C')

# def generate_prescription_pdf(data: dict, filename_base: str) -> str:
#     pdf = InternationalPDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=25) # Margin increased for safety

#     # --- DYNAMIC FONT LOADING ---
#     target_lang = data.get("language", "en")
#     font_filename = FONT_MAP.get(target_lang, "hindi.ttf") # Default to Hindi font (it supports English too)
    
#     # Font Path Fix: Check both backend/fonts and root/fonts
#     font_path = FONTS_DIR / font_filename
#     if not font_path.exists():
#         font_path = Path(os.getcwd()) / "fonts" / font_filename

#     has_unicode_font = False
#     if font_path.exists():
#         try:
#             pdf.add_font('LocalFont', '', str(font_path), uni=True)
#             has_unicode_font = True
#         except Exception as e:
#             print(f"Font Error: {e}")

#     def clean_text(text):
#         if not has_unicode_font:
#             return text.encode('latin-1', 'ignore').decode('latin-1')
#         return text

#     # --- 1. METADATA CARD ---
#     pdf.set_fill_color(*COLOR_SECTION_BG)
#     pdf.rect(10, 45, 190, 25, 'F')
    
#     pdf.set_y(50)
#     pdf.set_x(15)
#     pdf.set_text_color(*COLOR_TEXT_MAIN)
    
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(25, 6, "REPORT ID:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     # pdf.cell(60, 6, f"#{filename_base[:8].upper()}", 0, 0)
#     safe_id = filename_base

#     if not isinstance(safe_id, str):
#         safe_id = str(safe_id)

#     # safe_id = safe_id[:8].upper()
#     safe_id = str(filename_base)[:8]

#     pdf.cell(60, 6, f"#{safe_id}", 0, 0)
 
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(15, 6, "DATE:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     pdf.cell(0, 6, datetime.now().strftime("%d %B, %Y"), 0, 1)
    
#     # app/utils/pdf_generator.py (Inside generate_prescription_pdf, Metadata Block)

# # ... (Previous lines: Report ID & Date)

# # Row 2: FARMER ID & CROP STAGE (The clean, non-overlapping line)
#     pdf.set_x(15) # Cursor wapas shuru mein
    
# # 1. FARMER ID
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(25, 6, "FARMER ID:", 0, 0) # Width 25
#     pdf.set_font("Helvetica", '', 10)
#     pdf.cell(60, 6, str(data.get('farmer_id', 'Guest')), 0, 0) # Width 60
    
# # 2. CROP STAGE
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(30, 6, "CROP STAGE:", 0, 0) # Width 30
#     pdf.set_font("Helvetica", '', 10)
#     pdf.cell(0, 6, str(data.get('crop_stage', 'N/A')), 0, 1) # Rest of the line, ends row

#     pdf.ln(10) # Space after card
# # ... (Rest of the code continues) ...
    


#     # --- 2. DIAGNOSIS ---
#     pdf.set_font("Helvetica", 'B', 18)
#     pdf.set_text_color(*COLOR_DANGER)
#     # disease_display = data['disease'].replace("___", " ").replace("_", " ").upper()

#     raw_disease = data.get("disease", "Unknown")

#     if not isinstance(raw_disease, str):
#         raw_disease = str(raw_disease)

#     disease_display = raw_disease.replace("___", " ").replace("_", " ")


#     pdf.cell(0, 10, f"DETECTED: {disease_display}", 0, 1, 'L')
    
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.set_text_color(*COLOR_ACCENT)
#     conf = float(data['confidence']) * 100
#     pdf.cell(0, 6, f"Model Confidence Score: {conf:.1f}%", 0, 1, 'L')

#     img_path = data.get('image_path')
#     if img_path and os.path.exists(img_path):
#         pdf.ln(5)
#         # Check space before adding image
#         if pdf.get_y() > 200: pdf.add_page()
#         pdf.image(img_path, x=12, w=60, h=60)
#         pdf.ln(5)
#     else:
#         pdf.ln(10)

#     # --- 3. TREATMENT PLAN ---
#     if pdf.get_y() > 230: pdf.add_page()
    
#     pdf.ln(5)
#     pdf.set_fill_color(*COLOR_BRAND_BG)
#     pdf.set_text_color(255, 255, 255)
#     pdf.set_font("Helvetica", 'B', 12)
#     pdf.cell(190, 8, "  TREATMENT PLAN", 0, 1, 'L', fill=True)
#     pdf.ln(5)
    
#     if has_unicode_font: pdf.set_font("LocalFont", size=11)
#     else: pdf.set_font("Helvetica", '', 11)
    
#     pdf.set_text_color(*COLOR_TEXT_MAIN)
#     treatments = data.get('treatment', [])
#     for i, step in enumerate(treatments, 1):
#         step = clean_text(step)
#         pdf.multi_cell(0, 7, f"{i}. {step}", border=0)
#         pdf.ln(1)

#     # --- 4. PREVENTION PLAN ---
#     if pdf.get_y() > 220: pdf.add_page() # Early page break check
    
#     pdf.ln(5)
#     pdf.set_fill_color(255, 193, 7) # Amber
#     pdf.set_text_color(0, 0, 0)
#     pdf.set_font("Helvetica", 'B', 12)
#     pdf.cell(190, 8, "  PREVENTIVE MEASURES", 0, 1, 'L', fill=True)
#     pdf.ln(5)

#     if has_unicode_font: pdf.set_font("LocalFont", size=11)
#     else: pdf.set_font("Helvetica", '', 11)
        
#     pdf.set_text_color(*COLOR_TEXT_MAIN)
#     preventions = data.get('prevention', [])
#     for i, step in enumerate(preventions, 1):
#         step = clean_text(step)
#         pdf.multi_cell(0, 7, f"{i}. {step}", border=0)
#         pdf.ln(1)

#     # --- 5. QR CODE (Smart Layout) ---
#     pdf.ln(10)
#     y_pos = pdf.get_y()
    
#     # ✅ CRITICAL FIX: Agar page ke end ke paas hain (>200), to naya page lo
#     # Aur naye page par y_pos ko 50 set karo taaki Header ke neeche aaye
#     if y_pos > 210: 
#         pdf.add_page()
#         y_pos = 55 # Header ke neeche safe distance
        
#     # Generate QR
#     local_ip = get_local_ip()
#     audio_link = data.get('audio_url', '')
#     if audio_link and "localhost" in audio_link:
#         audio_link = audio_link.replace("localhost", local_ip)
#     elif audio_link and audio_link.startswith("/"):
#         audio_link = f"http://{local_ip}:8000{audio_link}"
        
#     qr = qrcode.make(audio_link)
#     temp_qr = UPLOAD_DIR / f"temp_qr_{filename_base}.png"
#     qr.save(temp_qr)
    
#     # Draw Box
#     pdf.set_draw_color(200, 200, 200)
#     pdf.set_fill_color(255, 255, 255)
#     pdf.rect(140, y_pos, 50, 55, 'FD') # Right aligned
    
#     pdf.image(str(temp_qr), x=145, y=y_pos+5, w=40, h=40)
    
#     pdf.set_xy(140, y_pos + 45)
#     pdf.set_font("Helvetica", 'B', 9)
#     pdf.set_text_color(*COLOR_BRAND_BG)
#     pdf.cell(50, 5, "SCAN FOR AUDIO", 0, 1, 'C')

#     if os.path.exists(temp_qr): os.remove(temp_qr)

#     pdf_filename = f"report_{filename_base}.pdf"
#     output_path = UPLOAD_DIR / pdf_filename
#     pdf.output(str(output_path))
    
#     return f"http://{local_ip}:8000/uploads/{pdf_filename}"



# from fpdf import FPDF
# import qrcode
# import os
# from pathlib import Path
# from datetime import datetime
# from ..config import get_settings

# settings = get_settings()
# UPLOAD_DIR = Path(settings.UPLOAD_DIR)

# # --- 🎨 PROFESSIONAL COLOR PALETTE ---
# # RGB Format
# COLOR_BRAND_BG = (33, 150, 83)      # AgroGuard Green
# COLOR_BRAND_TEXT = (255, 255, 255)  # White
# COLOR_SECTION_BG = (245, 247, 250)  # Light Gray-Blue (For Blocks)
# COLOR_TEXT_MAIN = (45, 55, 72)      # Dark Slate (Better than black)
# COLOR_DANGER = (220, 53, 69)        # Red (For Disease Name)
# COLOR_ACCENT = (50, 50, 50)

# class InternationalPDF(FPDF):
#     def header(self):
#         # --- BRAND HEADER ---
#         self.set_fill_color(*COLOR_BRAND_BG)
#         self.rect(0, 0, 210, 40, 'F') # Full width header
        
#         # Logo Text
#         self.set_y(15)
#         self.set_font('Helvetica', 'B', 24)
#         self.set_text_color(*COLOR_BRAND_TEXT)
#         self.cell(0, 10, 'AgroGuard AI', 0, 1, 'C')
        
#         # Sub-heading
#         self.set_font('Helvetica', '', 10)
#         self.cell(0, 5, 'Advanced Plant Disease Analysis Report', 0, 1, 'C')
#         self.ln(20)

#     def footer(self):
#         # --- FOOTER ---
#         self.set_y(-20)
#         self.set_font('Helvetica', 'I', 8)
#         self.set_text_color(150, 150, 150)
#         self.cell(0, 10, f'Generated by AgroGuard System | Page {self.page_no()}', 0, 0, 'C')

# def generate_prescription_pdf(data: dict, filename_base: str) -> str:
#     pdf = InternationalPDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=15)
    
#     # --- 1. METADATA BLOCK (Gray Box) ---
#     pdf.set_fill_color(*COLOR_SECTION_BG)
#     pdf.rect(10, 45, 190, 25, 'F')
    
#     pdf.set_y(50)
#     pdf.set_x(15)
#     pdf.set_text_color(*COLOR_TEXT_MAIN)
    
#     # Row 1: Report ID & Date
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(25, 6, "REPORT ID:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     pdf.cell(60, 6, f"#{filename_base[:8].upper()}", 0, 0)
    
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(15, 6, "DATE:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     pdf.cell(0, 6, datetime.now().strftime("%d %B, %Y"), 0, 1)
    
#     # Row 2: Farmer ID
#     pdf.set_x(15)
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.cell(25, 6, "FARMER:", 0, 0)
#     pdf.set_font("Helvetica", '', 10)
#     pdf.cell(0, 6, str(data.get('farmer_id', 'Guest')), 0, 1)
    
#     pdf.ln(15)

#     # --- 2. DIAGNOSIS & IMAGE SECTION ---
    
#     # Disease Name (Big Red Alert)
#     pdf.set_font("Helvetica", 'B', 18)
#     pdf.set_text_color(*COLOR_DANGER)
#     disease_display = data['disease'].replace("___", " ").replace("_", " ").upper()
#     pdf.cell(0, 10, f"DETECTED: {disease_display}", 0, 1, 'L')
    
#     # Confidence
#     pdf.set_font("Helvetica", 'B', 10)
#     pdf.set_text_color(*COLOR_ACCENT)
#     conf = float(data['confidence']) * 100
#     pdf.cell(0, 6, f"AI Confidence Score: {conf:.1f}%", 0, 1, 'L')
    
#     # Plant Image (Evidence)
#     # Agar image path valid hai, to usko show karo
#     img_path = data.get('image_path')
#     if img_path and os.path.exists(img_path):
#         pdf.ln(5)
#         # Image ko resize karke daalna (Square styling)
#         pdf.image(img_path, x=12, w=60, h=60) 
#         # Cursor ko wapas image ke neeche lao ya side mein (Simple layout ke liye neeche late hain)
#         pdf.ln(5)
#     else:
#         pdf.ln(10)

#     # --- 3. TREATMENT PLAN (Dynamic List) ---
#     # Hum yahan Hardcoded nahi, balki 'data' dictionary se list padhenge
    
#     pdf.ln(5)
#     pdf.set_fill_color(*COLOR_BRAND_BG)
#     pdf.set_text_color(255, 255, 255)
#     pdf.set_font("Helvetica", 'B', 12)
#     # Section Header Strip
#     pdf.cell(190, 10, "  RECOMMENDED TREATMENT PLAN", 0, 1, 'L', fill=True)
    
#     pdf.ln(5)
#     pdf.set_text_color(*COLOR_TEXT_MAIN)
#     pdf.set_font("Helvetica", '', 11)
    
#     treatments = data.get('treatment', [])
#     if not treatments:
#         pdf.cell(0, 8, "No specific treatment found. Consult an agronomist.", 0, 1)
#     else:
#         for i, step in enumerate(treatments, 1):
#             # Clean text
#             safe_text = step.encode('latin-1', 'replace').decode('latin-1')
#             # Bullet point style
#             pdf.multi_cell(0, 8, f"{i}. {safe_text}", border=0)
#             pdf.ln(1)

#     # --- 4. QR CODE SECTION (Audio Link) ---
#     pdf.ln(10)
    
#     # QR Logic
#     qr_content = f"Disease: {disease_display}\nListen: {data.get('audio_url', 'N/A')}"
#     qr = qrcode.make(qr_content)
#     temp_qr = UPLOAD_DIR / f"temp_qr_{filename_base}.png"
#     qr.save(temp_qr)
    
#     # QR Layout (Right Aligned box)
#     y_pos = pdf.get_y()
#     pdf.set_draw_color(200, 200, 200)
#     pdf.rect(140, y_pos, 50, 60) # Border box
    
#     pdf.image(str(temp_qr), x=145, y=y_pos+5, w=40, h=40)
    
#     # Instruction Text
#     pdf.set_xy(140, y_pos + 45)
#     pdf.set_font("Helvetica", 'B', 9)
#     pdf.cell(50, 5, "SCAN FOR AUDIO", 0, 1, 'C')
#     pdf.set_x(140)
#     pdf.set_font("Helvetica", '', 8)
#     pdf.cell(50, 5, "(Listen in Local Lang)", 0, 1, 'C')

#     # Cleanup
#     if os.path.exists(temp_qr):
#         os.remove(temp_qr)

#     # Output
#     pdf_filename = f"report_{filename_base}.pdf"
#     output_path = UPLOAD_DIR / pdf_filename
#     pdf.output(str(output_path))
    
#     return f"/uploads/{pdf_filename}"



# from fpdf import FPDF
# import qrcode
# import os
# from pathlib import Path
# from datetime import datetime
# from ..config import get_settings

# settings = get_settings()
# UPLOAD_DIR = Path(settings.UPLOAD_DIR)

# # fallback image path (the uploaded image you provided)
# FALLBACK_IMAGE_PATH = r"C:\Users\kille\agroguard\backend\uploads\temp_Screenshot 2025-11-17 231512.png"

# class DoctorPDF(FPDF):
#     def header(self):
#         # Top banner
#         self.set_fill_color(34, 139, 34)
#         self.rect(0, 0, 210, 28, 'F')
#         self.set_font('Arial', 'B', 18)
#         self.set_text_color(255, 255, 255)
#         self.set_xy(10, 6)
#         self.cell(0, 10, "AGROGUARD - DIAGNOSTIC PRESCRIPTION", 0, 0, 'C')
#         self.ln(14)

#     def footer(self):
#         self.set_y(-22)
#         self.set_font('Arial', 'I', 8)
#         self.set_text_color(120, 120, 120)
#         self.multi_cell(0, 4,
#             "Disclaimer: AI-generated advisory. Always consult a local agricultural expert before applying chemicals.",
#             0, 'C')
#         self.set_y(-10)
#         self.set_font('Arial', 'B', 8)
#         self.cell(0, 6, f"Page {self.page_no()} | AgroGuard", 0, 0, 'C')


# def sanitize_text(text: str) -> str:
#     """Convert to latin-1 safe string for default FPDF fonts."""
#     if text is None:
#         return ""
#     return str(text).encode('latin-1', 'replace').decode('latin-1')


# def draw_card_box(pdf: FPDF, x: float, y: float, w: float, h: float, radius: float = 3, fill_color=(245,245,245), border_color=(200,200,200)):
#     """Simple rectangle card (rounded corners not native in FPDF; using plain rect for compatibility)."""
#     pdf.set_fill_color(*fill_color)
#     pdf.set_draw_color(*border_color)
#     pdf.rect(x, y, w, h, 'DF')


# def generate_prescription_pdf(data: dict, filename_base: str) -> str:
#     """
#     Doctor-Style PDF v3
#     data keys expected:
#       - farmer_id
#       - disease
#       - confidence (0..1)
#       - treatment (list of strings)
#       - audio_url (optional)
#       - date (string)
#       - image_path (optional)  <-- path to the uploaded plant image
#     """
#     pdf = DoctorPDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=15)

#     # Basic fonts
#     pdf.set_font('Arial', '', 10)
#     pdf.set_text_color(0, 0, 0)

#     # --- HEADER INFO CARD ---
#     card_x, card_y, card_w, card_h = 12, 36, 186, 28
#     draw_card_box(pdf, card_x, card_y, card_w, card_h, fill_color=(245, 255, 245), border_color=(180, 220, 180))
#     pdf.set_xy(card_x + 6, card_y + 6)
#     pdf.set_font('Arial', 'B', 10)
#     pdf.cell(30, 6, "Report ID:", 0, 0)
#     pdf.set_font('Arial', '', 10)
#     pdf.cell(60, 6, filename_base[:10].upper(), 0, 0)

#     pdf.set_font('Arial', 'B', 10)
#     pdf.cell(20, 6, "Date:", 0, 0)
#     pdf.set_font('Arial', '', 10)
#     pdf.cell(0, 6, data.get('date', datetime.now().strftime("%Y-%m-%d %H:%M")), 0, 1)

#     pdf.set_xy(card_x + 6, card_y + 14)
#     pdf.set_font('Arial', 'B', 10)
#     pdf.cell(30, 6, "Farmer ID:", 0, 0)
#     pdf.set_font('Arial', '', 10)
#     pdf.cell(0, 6, sanitize_text(data.get('farmer_id', 'unknown')), 0, 1)

#     pdf.ln(8)

#     # --- DIAGNOSIS CARD (left) and PLANT IMAGE (right) layout ---
#     # Left column width ~ 110, right column ~ 70
#     left_w = 110
#     right_w = 70
#     start_x = 12
#     start_y = pdf.get_y()

#     # Diagnosis box background
#     draw_card_box(pdf, start_x, start_y, left_w, 78, fill_color=(255,255,255), border_color=(220,220,220))

#     pdf.set_xy(start_x + 6, start_y + 6)
#     pdf.set_font('Arial', 'B', 12)
#     pdf.set_text_color(34, 139, 34)
#     pdf.cell(0, 6, "Diagnosis", 0, 1)

#     # disease name with auto-scaling font
#     disease_raw = sanitize_text(data.get('disease', '')).replace('___', ' ').replace('_', ' ')
#     if len(disease_raw) > 40:
#         pdf.set_font('Arial', 'B', 12)
#     elif len(disease_raw) > 24:
#         pdf.set_font('Arial', 'B', 14)
#     else:
#         pdf.set_font('Arial', 'B', 16)
#     pdf.set_text_color(180, 30, 30)
#     pdf.multi_cell(left_w - 12, 8, disease_raw)

#     # Confidence
#     pdf.set_font('Arial', '', 10)
#     pdf.set_text_color(0, 0, 0)
#     conf = float(data.get('confidence', 0.0)) * 100
#     pdf.cell(0, 6, f"AI Confidence: {conf:.2f}%", 0, 1)

#     # Move to right column and place image
#     img_x = start_x + left_w + 6
#     img_y = start_y + 6
#     img_w = right_w - 12
#     image_path = data.get('image_path') or FALLBACK_IMAGE_PATH

#     # Try to add image (safe checks)
#     try:
#         if image_path and Path(image_path).exists():
#             # maintain aspect ratio, max width img_w and max height 70
#             pdf.image(str(image_path), x=img_x, y=img_y, w=img_w)
#         else:
#             # Placeholder box if image missing
#             pdf.set_xy(img_x, img_y + 24)
#             pdf.set_font('Arial', 'I', 9)
#             pdf.set_text_color(120, 120, 120)
#             pdf.multi_cell(right_w - 6, 6, "Plant image not available", 0, 'C')
#     except Exception:
#         pdf.set_xy(img_x, img_y + 24)
#         pdf.set_font('Arial', 'I', 9)
#         pdf.set_text_color(120, 120, 120)
#         pdf.multi_cell(right_w - 6, 6, "Error loading image", 0, 'C')

#     pdf.ln(84)  # move below diagnosis+image area

#     # --- TREATMENT CARD ---
#     draw_card_box(pdf, 12, pdf.get_y(), 186, 60, fill_color=(255,255,255), border_color=(220,220,220))
#     pdf.set_xy(18, pdf.get_y() + 6)
#     pdf.set_font('Arial', 'B', 12)
#     pdf.set_text_color(34, 139, 34)
#     pdf.cell(0, 6, "Recommended Treatment", 0, 1)
#     pdf.ln(2)

#     pdf.set_font('Arial', '', 10)
#     pdf.set_text_color(0, 0, 0)
#     treatments = data.get('treatment', ["Consult a local plant expert."])
#     for i, step in enumerate(treatments, 1):
#         pdf.multi_cell(170, 6, f"{i}. {sanitize_text(step)}")
#         pdf.ln(1)

#     pdf.ln(4)

#     # --- CHEMICAL RECOMMENDATIONS (Option A - BASIC) ---
#     draw_card_box(pdf, 12, pdf.get_y(), 186, 48, fill_color=(255,255,255), border_color=(220,220,220))
#     pdf.set_xy(18, pdf.get_y() + 6)
#     pdf.set_font('Arial', 'B', 12)
#     pdf.set_text_color(34, 139, 34)
#     pdf.cell(0, 6, "Chemical Recommendations (Basic)", 0, 1)
#     pdf.ln(2)

#     pdf.set_font('Arial', '', 10)
#     pdf.set_text_color(0, 0, 0)

#     # Basic list (Option A). You can map disease -> chemicals dynamically later.
#     chemicals = [
#         "Mancozeb 75% WP – Mix 25g in 10L water",
#         "Copper Oxychloride 50% – Mix 30g in 10L water",
#         "Neem oil (organic) – 5ml per liter (alternative/organic)"
#     ]
#     for i, chem in enumerate(chemicals, 1):
#         pdf.multi_cell(170, 6, f"{i}. {sanitize_text(chem)}")
#         pdf.ln(1)

#     pdf.ln(6)

#     # --- LOCATION & AUDIO QR area (bottom) ---
#     pdf.set_font('Arial', 'B', 11)
#     pdf.set_text_color(0, 0, 0)
#     pdf.cell(0, 6, "Location & Audio", 0, 1)
#     pdf.ln(2)

#     lat = data.get('latitude')
#     lon = data.get('longitude')
#     loc_text = "Not provided"
#     if lat and lon:
#         loc_text = f"Latitude: {lat}, Longitude: {lon}"

#     pdf.set_font('Arial', '', 10)
#     pdf.multi_cell(0, 6, f"Location: {sanitize_text(loc_text)}")

#     # QR generation for audio link (if present)
#     audio = data.get('audio_url', '')
#     qr_payload = f"Disease: {disease_raw}\nAudio: {audio}\nReportID: {filename_base}"
#     qr_path = UPLOAD_DIR / f"qr_{filename_base}.png"
#     try:
#         qrcode.make(qr_payload).save(qr_path)
#         pdf.image(str(qr_path), x=15, y=pdf.get_y()+4, w=35)
#         pdf.set_xy(55, pdf.get_y()+8)
#         pdf.set_font('Arial', '', 9)
#         pdf.multi_cell(0, 6, "Scan QR to listen to audio advice.", 0, 'L')
#     except Exception:
#         pdf.set_font('Arial', 'I', 9)
#         pdf.set_text_color(120, 120, 120)
#         pdf.multi_cell(0, 6, "QR not available.", 0, 'L')

#     # Cleanup QR file
#     if qr_path.exists():
#         try:
#             os.remove(qr_path)
#         except Exception:
#             pass

#     # --- SAVE PDF ---
#     pdf_filename = f"prescription_{filename_base}.pdf"
#     pdf_path = UPLOAD_DIR / pdf_filename
#     pdf.output(str(pdf_path))

#     return f"/uploads/{pdf_filename}"





# from fpdf import FPDF
# import qrcode
# import os
# from pathlib import Path
# from datetime import datetime
# from ..config import get_settings

# settings = get_settings()
# UPLOAD_DIR = Path(settings.UPLOAD_DIR)

# class PDF(FPDF):
#     def header(self):
#         # Header Banner
#         self.set_fill_color(34, 139, 34)
#         self.rect(0, 0, 210, 28, 'F')

#         # Header Title
#         self.set_font('Arial', 'B', 20)
#         self.set_text_color(255, 255, 255)
#         self.set_xy(10, 7)
#         self.cell(0, 10, 'AgroGuard Report', 0, 1, 'C')
#         self.ln(5)

#     def footer(self):
#         self.set_y(-20)
#         self.set_font('Arial', 'I', 8)
#         self.set_text_color(120, 120, 120)
#         self.multi_cell(0, 4, "Disclaimer: This diagnosis is AI-generated. Always verify with an agriculture expert.", 0, 'C')

#         self.set_y(-10)
#         self.set_font('Arial', 'B', 8)
#         self.cell(0, 5, f"Page {self.page_no()} | AgroGuard", 0, 0, 'C')


# def sanitize_text(text):
#     """
#     Convert any non-latin characters safely.
#     FPDF's default fonts do NOT support Unicode.
#     """
#     return text.encode('latin-1', 'replace').decode('latin-1')


# def generate_prescription_pdf(data: dict, filename_base: str) -> str:
#     pdf = PDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=15)

#     # === Report Info Box ===
#     pdf.set_fill_color(245, 255, 245)
#     pdf.set_draw_color(34, 139, 34)
#     pdf.rect(10, 35, 190, 30, 'DF')

#     pdf.set_xy(15, 40)
#     pdf.set_font('Arial', 'B', 10)
#     pdf.set_text_color(0, 0, 0)
#     pdf.cell(35, 6, "Report ID:", 0, 0)
#     pdf.set_font('Arial', '', 10)
#     pdf.cell(60, 6, filename_base[:10].upper(), 0, 0)

#     pdf.set_font('Arial', 'B', 10)
#     pdf.cell(20, 6, "Date:", 0, 0)
#     pdf.set_font('Arial', '', 10)
#     pdf.cell(0, 6, data.get('date', ''), 0, 1)

#     # Farmer
#     pdf.set_xy(15, 47)
#     pdf.set_font('Arial', 'B', 10)
#     pdf.cell(35, 6, "Farmer ID:", 0, 0)
#     pdf.set_font('Arial', '', 10)
#     pdf.cell(0, 6, sanitize_text(data.get('farmer_id', 'unknown')), 0, 1)

#     pdf.ln(12)

#     # === Diagnosis Section ===
#     pdf.set_font('Arial', 'B', 14)
#     pdf.set_text_color(34, 139, 34)
#     pdf.cell(0, 8, "Diagnosis", 0, 1)
#     pdf.ln(2)

#     # Disease Name
#     disease = sanitize_text(data.get('disease', '')).replace('___', ' ').replace('_', ' ')

#     # Auto font scaling for long disease names
#     if len(disease) > 40:
#         pdf.set_font('Arial', 'B', 14)
#     elif len(disease) > 25:
#         pdf.set_font('Arial', 'B', 16)
#     else:
#         pdf.set_font('Arial', 'B', 20)

#     pdf.set_text_color(220, 53, 69)
#     pdf.multi_cell(0, 10, disease)

#     # Confidence
#     pdf.set_text_color(0, 0, 0)
#     pdf.set_font('Arial', '', 10)
#     pdf.cell(0, 6, f"AI Confidence: {float(data['confidence'])*100:.2f}%", 0, 1)
#     pdf.ln(8)

#     # === Treatment Section ===
#     pdf.set_font('Arial', 'B', 14)
#     pdf.set_text_color(34, 139, 34)
#     pdf.cell(0, 8, "Recommended Treatment", 0, 1)
#     pdf.ln(3)

#     treatment_list = data.get('treatment', [])
#     pdf.set_text_color(0, 0, 0)
#     pdf.set_font('Arial', '', 10)

#     for step in treatment_list:
#         safe_step = sanitize_text(step)
#         pdf.multi_cell(0, 6, f"- {safe_step}")
#         pdf.ln(1)

#     pdf.ln(5)

#     # === QR Code ===
#     audio_url = sanitize_text(data.get('audio_url', ''))
#     qr_text = f"{disease}\nAudio: {audio_url}"

#     qr_path = UPLOAD_DIR / f"qr_{filename_base}.png"
#     qrcode.make(qr_text).save(qr_path)

#     pdf.set_font('Arial', 'B', 12)
#     pdf.set_text_color(34, 139, 34)
#     pdf.cell(0, 10, "Scan for Audio Guide", 0, 1)

#     pdf.image(str(qr_path), x=15, w=40)
#     pdf.ln(3)

#     pdf.set_font('Arial', '', 9)
#     pdf.set_text_color(90, 90, 90)
#     pdf.multi_cell(0, 5, "Use your phone to scan the QR code and listen to disease treatment advice.", 0, 'L')

#     if qr_path.exists():
#         os.remove(qr_path)

#     # === Save PDF ===
#     pdf_filename = f"prescription_{filename_base}.pdf"
#     pdf_path = UPLOAD_DIR / pdf_filename

#     pdf.output(str(pdf_path))

#     return f"/uploads/{pdf_filename}"






# from fpdf import FPDF
# import qrcode
# import os
# from pathlib import Path
# from datetime import datetime
# from ..config import get_settings

# settings = get_settings()
# UPLOAD_DIR = Path(settings.UPLOAD_DIR)

# # --- 🎨 COLOR PALETTE (Professional Theme) ---
# COLOR_PRIMARY = (34, 139, 34)    # Forest Green (Brand Color)
# COLOR_SECONDARY = (240, 248, 240) # Very Light Green (Backgrounds)
# COLOR_DANGER = (220, 53, 69)     # Red (For Disease Name)
# COLOR_TEXT = (50, 50, 50)        # Dark Gray (Better than black)
# COLOR_LIGHT_GRAY = (200, 200, 200) # For Borders

# class ProfessionalPDF(FPDF):
#     def header(self):
#         # --- TOP BANNER ---
#         self.set_fill_color(*COLOR_PRIMARY)
#         self.rect(0, 0, 210, 35, 'F') # Full width green header
        
#         # Title
#         self.set_y(10)
#         self.set_font('Arial', 'B', 24)
#         self.set_text_color(255, 255, 255) # White text
#         self.cell(0, 10, 'AgroGuard', 0, 1, 'C')
        
#         # Subtitle
#         self.set_font('Arial', '', 10)
#         self.cell(0, 5, 'AI-Powered Disease Detection & Advisory Report', 0, 1, 'C')
#         self.ln(20) # Spacing after header

#     def footer(self):
#         # --- FOOTER SECTION ---
#         self.set_y(-30)
#         self.set_font('Arial', 'I', 8)
#         self.set_text_color(100, 100, 100)
        
#         # Disclaimer
#         self.multi_cell(0, 4, "DISCLAIMER: This report is generated by AI. Please consult an agricultural expert before applying heavy chemicals. AgroGuard is an assistive tool.", 0, 'C')
        
#         # Page Number
#         self.set_y(-15)
#         self.set_font('Arial', 'B', 8)
#         self.cell(0, 10, f'Page {self.page_no()} | AgroGuard Official', 0, 0, 'C')

# def generate_prescription_pdf(prediction_data: dict, filename_base: str) -> str:
#     """
#     Generates a High-Quality, International Standard PDF.
#     """
#     pdf = ProfessionalPDF()
#     pdf.add_page()
#     pdf.set_auto_page_break(auto=True, margin=20)

#     # --- 1. FARMER & SCAN DETAILS (Card Style) ---
#     pdf.set_fill_color(*COLOR_SECONDARY) # Light Green BG
#     pdf.set_draw_color(*COLOR_PRIMARY)   # Green Border
#     pdf.rect(10, 40, 190, 35, 'DF')      # Draw Rectangle
    
#     pdf.set_y(45)
#     pdf.set_x(15)
    
#     # Left Side: ID and Date
#     pdf.set_font("Arial", 'B', 10)
#     pdf.set_text_color(*COLOR_TEXT)
#     pdf.cell(30, 8, "REPORT ID:", 0, 0)
#     pdf.set_font("Arial", '', 10)
#     pdf.cell(60, 8, f"#{filename_base[:8].upper()}", 0, 0)
    
#     # Right Side: Date
#     pdf.set_font("Arial", 'B', 10)
#     pdf.cell(20, 8, "DATE:", 0, 0)
#     pdf.set_font("Arial", '', 10)
#     pdf.cell(0, 8, prediction_data.get('date', datetime.now().strftime("%Y-%m-%d")), 0, 1)
    
#     pdf.set_x(15)
#     pdf.set_font("Arial", 'B', 10)
#     pdf.cell(30, 8, "FARMER ID:", 0, 0)
#     pdf.set_font("Arial", '', 10)
#     pdf.cell(0, 8, prediction_data.get('farmer_id', 'Unknown'), 0, 1)

#     pdf.ln(15) # Space after card

#     # --- 2. DIAGNOSIS SECTION (The Main Result) ---
#     pdf.set_font("Arial", 'B', 14)
#     pdf.set_text_color(*COLOR_PRIMARY)
#     pdf.cell(0, 10, "DIAGNOSIS RESULT", 0, 1, 'L')
    
#     # Draw Line
#     pdf.set_draw_color(*COLOR_LIGHT_GRAY)
#     pdf.line(10, pdf.get_y(), 200, pdf.get_y())
#     pdf.ln(5)

#     # Disease Name (BIG RED TEXT)
#     pdf.set_font("Arial", 'B', 20)
#     pdf.set_text_color(*COLOR_DANGER) # RED
#     disease_name = prediction_data['disease'].replace('___', ' ').replace('_', ' ').upper()
#     pdf.cell(0, 12, disease_name, 0, 1, 'L')
    
#     # Confidence Bar (Text representation)
#     conf = float(prediction_data['confidence']) * 100
#     pdf.set_font("Arial", '', 10)
#     pdf.set_text_color(0, 0, 0)
#     pdf.cell(0, 8, f"AI Confidence Level: {conf:.2f}%", 0, 1, 'L')
#     pdf.ln(10)

#     # --- 3. TREATMENT PLAN (Boxed) ---
#     pdf.set_font("Arial", 'B', 14)
#     pdf.set_text_color(*COLOR_PRIMARY)
#     pdf.cell(0, 10, "RECOMMENDED TREATMENT", 0, 1, 'L')
#     pdf.line(10, pdf.get_y(), 200, pdf.get_y())
#     pdf.ln(5)

#     pdf.set_font("Arial", '', 11)
#     pdf.set_text_color(30, 30, 30)
    
#     treatments = prediction_data.get('treatment', [])
#     if not treatments:
#         treatments = ["Consult a local plant expert for specific advice."]
        
#     for i, step in enumerate(treatments, 1):
#         # Clean text to prevent unicode crash in standard fonts
#         safe_text = step.encode('latin-1', 'replace').decode('latin-1')
#         pdf.multi_cell(0, 8, f"{i}. {safe_text}")
    
#     pdf.ln(10)

#     # --- 4. QR CODE & AUDIO SECTION (Bottom Right) ---
#     # Hum QR code ko right side mein dikhayenge aur text ko left mein
    
#     y_before_qr = pdf.get_y()
    
#     # Generate QR
#     qr_data = f"Disease: {disease_name}\nAudio: {prediction_data.get('audio_url', 'No Audio')}"
#     qr = qrcode.make(qr_data)
#     temp_qr_path = UPLOAD_DIR / f"temp_qr_{filename_base}.png"
#     qr.save(temp_qr_path)

#     # Draw a Box for QR Area
#     pdf.set_fill_color(250, 250, 250)
#     pdf.rect(10, y_before_qr, 190, 40, 'F')
    
#     # QR Image (Left Side)
#     pdf.image(str(temp_qr_path), x=15, y=y_before_qr+2, w=35)
    
#     # Text Instructions (Right Side of QR)
#     pdf.set_xy(55, y_before_qr + 5)
#     pdf.set_font("Arial", 'B', 12)
#     pdf.set_text_color(*COLOR_PRIMARY)
#     pdf.cell(0, 8, "SCAN FOR AUDIO ADVICE", 0, 1)
    
#     pdf.set_xy(55, y_before_qr + 15)
#     pdf.set_font("Arial", '', 9)
#     pdf.set_text_color(100, 100, 100)
#     pdf.multi_cell(0, 5, "Use your phone camera to scan this QR code. You will be able to listen to the treatment advice in your local language.")

#     # Cleanup
#     if os.path.exists(temp_qr_path):
#         os.remove(temp_qr_path)

#     # --- SAVE PDF ---
#     pdf_filename = f"prescription_{filename_base}.pdf"
#     pdf_path = UPLOAD_DIR / pdf_filename
#     pdf.output(str(pdf_path))
    
#     return f"/uploads/{pdf_filename}"