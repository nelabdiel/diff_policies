import os
import logging
from typing import Tuple, Optional

# Try to import PDF processing libraries
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    import pdfplumber
    PDFPLUMBER_SUPPORT = True
except ImportError:
    PDFPLUMBER_SUPPORT = False

try:
    from bs4 import BeautifulSoup
    HTML_SUPPORT = True
except ImportError:
    HTML_SUPPORT = False

class DocumentProcessor:
    """Handles processing of different document formats"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_file(self, file_path: str) -> Tuple[Optional[str], str]:
        """
        Process a file and extract its content
        
        Args:
            file_path: Path to the uploaded file
            
        Returns:
            Tuple of (content, document_type)
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return self._process_pdf(file_path), 'pdf'
            elif file_extension in ['.html', '.htm']:
                return self._process_html(file_path), 'html'
            elif file_extension == '.txt':
                return self._process_text(file_path), 'text'
            else:
                self.logger.error(f"Unsupported file type: {file_extension}")
                return None, 'unknown'
                
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            return None, 'error'
    
    def _process_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from PDF file"""
        if not PDF_SUPPORT and not PDFPLUMBER_SUPPORT:
            self.logger.error("No PDF processing libraries available")
            return None
            
        try:
            # Try pdfplumber first (better for complex layouts)
            if PDFPLUMBER_SUPPORT:
                with pdfplumber.open(file_path) as pdf:
                    text_content = []
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)
                    
                    if text_content:
                        return '\n\n'.join(text_content)
            
            # Fallback to PyPDF2
            if PDF_SUPPORT:
                self.logger.info("pdfplumber not available, trying PyPDF2")
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content = []
                    
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                    
                    return '\n\n'.join(text_content) if text_content else None
                
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            return None
    
    def _process_html(self, file_path: str) -> Optional[str]:
        """Extract text from HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            if HTML_SUPPORT:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text and clean it up
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return text if text else None
            else:
                # Basic HTML tag removal without BeautifulSoup
                import re
                # Remove script and style blocks
                content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                # Remove HTML tags
                content = re.sub(r'<[^>]+>', '', content)
                # Clean up whitespace
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                return '\n'.join(lines) if lines else None
            
        except Exception as e:
            self.logger.error(f"Error processing HTML: {str(e)}")
            return None
    
    def _process_text(self, file_path: str) -> Optional[str]:
        """Process plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return content.strip() if content.strip() else None
            
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    content = file.read()
                return content.strip() if content.strip() else None
            except Exception as e:
                self.logger.error(f"Error processing text file with latin-1: {str(e)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing text file: {str(e)}")
            return None
    
    def extract_sections_from_text(self, text: str) -> list:
        """
        Extract structured sections from text based on common government memo patterns
        
        Args:
            text: The document text
            
        Returns:
            List of dictionaries with section info
        """
        import re
        
        sections = []
        
        # Common patterns for government memo sections
        section_patterns = [
            r'^(\d+\.\s+[A-Z][^.]*\.?)$',  # Numbered sections like "1. INTRODUCTION"
            r'^([A-Z][A-Z\s]+)$',  # All caps headers
            r'^(SECTION\s+\d+[:\-]?\s*[A-Z][^.]*\.?)$',  # Section headers
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):?$',  # Title case headers
        ]
        
        lines = text.split('\n')
        current_section = {'title': 'Introduction', 'content': [], 'start_line': 0}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this line matches any section pattern
            is_section_header = False
            for pattern in section_patterns:
                if re.match(pattern, line):
                    # Save previous section if it has content
                    if current_section['content']:
                        current_section['content'] = '\n'.join(current_section['content'])
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        'title': line,
                        'content': [],
                        'start_line': i
                    }
                    is_section_header = True
                    break
            
            if not is_section_header:
                current_section['content'].append(line)
        
        # Add the last section
        if current_section['content']:
            current_section['content'] = '\n'.join(current_section['content'])
            sections.append(current_section)
        
        return sections if sections else [{'title': 'Full Document', 'content': text, 'start_line': 0}]
