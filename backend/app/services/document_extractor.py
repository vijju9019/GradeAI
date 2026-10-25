import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

class DocumentExtractorService:
    def __init__(self):
        self.tesseract_available = self._check_tesseract()

    def _check_tesseract(self) -> bool:
        """Check if Tesseract binary is accessible in system PATH or configured path."""
        try:
            import pytesseract
            # Test running pytesseract
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR detected, version: {version}")
            return True
        except Exception as e:
            logger.info(f"Tesseract OCR not installed or not in PATH: {e}")
            return False

    def is_ocr_available(self) -> bool:
        return self.tesseract_available

    def preprocess_image(self, image_path: Path) -> Image.Image:
        """
        Preprocess image for better OCR:
        - Convert to grayscale
        - Resize if too small
        - Auto-contrast and sharpen
        """
        with Image.open(image_path) as img:
            # Convert to RGB/L
            img = img.convert('L')
            # Resize if resolution is low
            if img.width < 1200:
                scale = 1200 / float(img.width)
                new_size = (int(img.width * scale), int(img.height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Contrast enhancement
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.8)
            # Subtle sharpening
            img = img.filter(ImageFilter.SHARPEN)
            return img.copy()

    def extract_document(self, file_path: Path, mime_type: str) -> List[Dict[str, Any]]:
        """
        Extract text from document. Returns list of page dicts:
        [{ 'page_number': 1, 'text': '...', 'method': '...', 'is_poor_quality': bool, 'warning': '...' }]
        """
        extension = file_path.suffix.lower()

        if extension == ".txt":
            return self._extract_plain_text(file_path)
        elif extension == ".pdf":
            return self._extract_pdf(file_path)
        elif extension in [".png", ".jpg", ".jpeg"]:
            return self._extract_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def _extract_plain_text(self, file_path: Path) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return [{
                "page_number": 1,
                "text": content.strip(),
                "method": "plain_text",
                "is_poor_quality": len(content.strip()) < 10,
                "warning": "Empty document" if len(content.strip()) == 0 else None
            }]
        except Exception as e:
            logger.error(f"Failed to read plain text file: {e}")
            return [{
                "page_number": 1,
                "text": "",
                "method": "plain_text",
                "is_poor_quality": True,
                "warning": f"Extraction error: {str(e)}"
            }]

    def _extract_pdf(self, file_path: Path) -> List[Dict[str, Any]]:
        pages = []
        # Attempt 1: Direct digital text extraction with PyMuPDF
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(file_path))
            page_count = len(doc)
            
            for page_idx in range(page_count):
                page = doc.load_page(page_idx)
                extracted_text = page.get_text("text").strip()
                
                # Check if page has digital text
                if len(extracted_text) >= 20:
                    pages.append({
                        "page_number": page_idx + 1,
                        "text": extracted_text,
                        "method": "pdf_digital",
                        "is_poor_quality": False,
                        "warning": None
                    })
                else:
                    # Page seems scanned or has negligible digital text
                    # Try OCR if Tesseract is available
                    ocr_text, method, warning = self._ocr_pdf_page(page)
                    pages.append({
                        "page_number": page_idx + 1,
                        "text": ocr_text,
                        "method": method,
                        "is_poor_quality": len(ocr_text) < 15,
                        "warning": warning
                    })
            doc.close()
            return pages
        except Exception as e:
            logger.warning(f"PyMuPDF failed on {file_path}: {e}. Trying pdfplumber fallback.")

        # Attempt 2: pdfplumber fallback
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    pages.append({
                        "page_number": idx + 1,
                        "text": text.strip(),
                        "method": "pdf_digital_fallback",
                        "is_poor_quality": len(text.strip()) < 15,
                        "warning": "No digital text found; page may be scanned or empty" if len(text.strip()) == 0 else None
                    })
            return pages
        except Exception as e:
            logger.error(f"Failed to extract PDF: {e}")
            return [{
                "page_number": 1,
                "text": "",
                "method": "manual",
                "is_poor_quality": True,
                "warning": f"Failed to extract PDF: {str(e)}. Please enter text manually."
            }]

    def _ocr_pdf_page(self, fitz_page) -> tuple[str, str, Optional[str]]:
        """Render a PyMuPDF page to image and run Tesseract if available."""
        if not self.tesseract_available:
            return (
                "",
                "manual",
                "Scanned page detected, but Tesseract OCR is not installed on this system. You can enter or edit the answer text manually."
            )
        try:
            import pytesseract
            pix = fitz_page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            # Run Tesseract
            text = pytesseract.image_to_string(img)
            return (
                text.strip(),
                "tesseract_ocr",
                "OCR applied to scanned page. Note: ordinary OCR recognizes printed text reliably; please review or correct handwritten text."
            )
        except Exception as e:
            logger.error(f"OCR failed on page: {e}")
            return (
                "",
                "manual",
                f"OCR processing failed: {str(e)}. Please correct answer text manually."
            )

    def _extract_image(self, file_path: Path) -> List[Dict[str, Any]]:
        if not self.tesseract_available:
            return [{
                "page_number": 1,
                "text": "",
                "method": "manual",
                "is_poor_quality": True,
                "warning": "Image upload received, but Tesseract OCR is not installed on this host. You can input the student's answer text directly in the editor."
            }]
        try:
            import pytesseract
            preprocessed = self.preprocess_image(file_path)
            ocr_text = pytesseract.image_to_string(preprocessed)
            return [{
                "page_number": 1,
                "text": ocr_text.strip(),
                "method": "tesseract_ocr",
                "is_poor_quality": len(ocr_text.strip()) < 15,
                "warning": "Printed text OCR performed. Handwriting recognition requires manual verification." if len(ocr_text.strip()) > 0 else "No text detected in image."
            }]
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return [{
                "page_number": 1,
                "text": "",
                "method": "manual",
                "is_poor_quality": True,
                "warning": f"OCR extraction error: {str(e)}. Please enter text manually."
            }]


document_extractor = DocumentExtractorService()
