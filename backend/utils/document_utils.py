"""Document processing utilities for TenderWise."""

import os
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import asyncio
from datetime import datetime

# PDF processing
try:
    import PyPDF2
    import fitz  # PyMuPDF for better text extraction
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️  PDF processing libraries not available. Install with: pip install PyPDF2 PyMuPDF")

# Word document processing
try:
    import docx
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️  Word processing library not available. Install with: pip install python-docx")

async def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file using PyMuPDF for better results."""
    if not PDF_AVAILABLE:
        raise ImportError("PDF processing libraries not available")
    
    try:
        text_content = []
        
        # Use PyMuPDF (fitz) for better text extraction
        doc = fitz.open(file_path)
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            if text.strip():
                text_content.append(f"=== Página {page_num + 1} ===\n{text}\n")
        
        doc.close()
        
        if not text_content:
            # Fallback to PyPDF2 if PyMuPDF doesn't work
            return await _extract_with_pypdf2(file_path)
        
        return "\n".join(text_content)
        
    except Exception as e:
        print(f"❌ Error extracting text from PDF with PyMuPDF: {e}")
        # Fallback to PyPDF2
        try:
            return await _extract_with_pypdf2(file_path)
        except Exception as fallback_error:
            print(f"❌ Fallback PDF extraction also failed: {fallback_error}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

async def _extract_with_pypdf2(file_path: str) -> str:
    """Fallback PDF extraction using PyPDF2."""
    text_content = []
    
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            if text.strip():
                text_content.append(f"=== Página {page_num + 1} ===\n{text}\n")
    
    return "\n".join(text_content)

async def extract_text_from_docx(file_path: str) -> str:
    """Extract text from Word document."""
    if not DOCX_AVAILABLE:
        raise ImportError("Word processing library not available")
    
    try:
        doc = Document(file_path)
        text_content = []
        
        # Extract paragraphs
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)
        
        # Extract tables
        for table in doc.tables:
            table_text = []
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    row_text.append(cell.text.strip())
                table_text.append(" | ".join(row_text))
            
            if table_text:
                text_content.append("\n=== TABLA ===")
                text_content.extend(table_text)
                text_content.append("=== FIN TABLA ===\n")
        
        return "\n".join(text_content)
        
    except Exception as e:
        print(f"❌ Error extracting text from DOCX: {e}")
        raise Exception(f"Failed to extract text from Word document: {str(e)}")

async def extract_text_from_file(file_path: str) -> str:
    """Extract text from various file formats."""
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        return await extract_text_from_pdf(file_path)
    elif file_ext in ['.docx', '.doc']:
        return await extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")

def detect_document_type(text_content: str) -> str:
    """Detect the type of tender document based on content."""
    text_lower = text_content.lower()
    
    # Tender-specific keywords
    tender_keywords = {
        "pliego": ["pliego", "términos de referencia", "especificaciones técnicas"],
        "propuesta": ["propuesta técnica", "propuesta económica", "oferta"],
        "contrato": ["contrato", "cláusulas contractuales", "objeto del contrato"],
        "adjudicacion": ["adjudicación", "acta de adjudicación", "ganador"],
        "evaluacion": ["evaluación", "calificación", "puntaje"]
    }
    
    scores = {}
    for doc_type, keywords in tender_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        scores[doc_type] = score
    
    # Return the type with highest score
    if scores:
        return max(scores, key=scores.get)
    
    return "unknown"

def extract_contract_sections(text_content: str) -> Dict[str, str]:
    """Extract main sections from contract text."""
    sections = {}
    
    # Common contract section patterns
    section_patterns = {
        "objeto": r"(primera|objeto|alcance).*?del\s+contrato",
        "monto": r"(segunda|valor|monto).*?contrato",
        "plazo": r"(tercera|plazo|tiempo).*?ejecución",
        "garantias": r"(cuarta|garantías?).*?",
        "anticipo": r"(quinta|anticipo).*?",
        "multas": r"(sexta|multas?|penalizaciones?).*?",
        "recepcion": r"(séptima|recepción).*?obra",
        "controversias": r"(octava|resolución|controversias?).*?",
        "legislacion": r"(novena|legislación|normativa).*?aplicable"
    }
    
    for section_name, pattern in section_patterns.items():
        matches = re.finditer(pattern, text_content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            # Extract text around the match
            start = max(0, match.start() - 100)
            end = min(len(text_content), match.end() + 500)
            sections[section_name] = text_content[start:end].strip()
            break  # Take first match
    
    return sections

def extract_financial_data(text_content: str) -> Dict[str, Any]:
    """Extract financial information from contract text."""
    financial_data = {}
    
    # Amount patterns (USD format)
    amount_patterns = [
        r"USD?\s*([\d,]+\.?\d*)",
        r"\$\s*([\d,]+\.?\d*)",
        r"([\d,]+\.?\d*)\s*dólares?"
    ]
    
    amounts = []
    for pattern in amount_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        for match in matches:
            try:
                # Clean and convert amount
                clean_amount = match.replace(",", "")
                amount = float(clean_amount)
                if amount > 1000:  # Filter small numbers
                    amounts.append(amount)
            except ValueError:
                continue
    
    if amounts:
        financial_data["amounts_found"] = sorted(set(amounts), reverse=True)
        financial_data["max_amount"] = max(amounts)
    
    # Percentage patterns
    percentage_patterns = [
        r"(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*por\s*ciento"
    ]
    
    percentages = []
    for pattern in percentage_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        for match in matches:
            try:
                percentage = float(match)
                if 0 < percentage <= 100:  # Valid percentage range
                    percentages.append(percentage)
            except ValueError:
                continue
    
    if percentages:
        financial_data["percentages_found"] = sorted(set(percentages))
    
    # Timeline patterns
    timeline_patterns = [
        r"(\d+)\s*meses?",
        r"(\d+)\s*días?",
        r"(\d+)\s*años?"
    ]
    
    timelines = []
    for pattern in timeline_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        for match in matches:
            try:
                timeline = int(match)
                if 1 <= timeline <= 60:  # Reasonable timeline range
                    timelines.append(timeline)
            except ValueError:
                continue
    
    if timelines:
        financial_data["timelines_found"] = sorted(set(timelines))
    
    return financial_data

def extract_entities(text_content: str) -> Dict[str, List[str]]:
    """Extract entities like companies, locations, and RUCs."""
    entities = {
        "companies": [],
        "locations": [],
        "rucs": [],
        "persons": []
    }
    
    # RUC pattern (Ecuador: 13 digits)
    ruc_pattern = r"\b\d{13}\b"
    rucs = re.findall(ruc_pattern, text_content)
    entities["rucs"] = list(set(rucs))
    
    # Company patterns (S.A., CIA, LTDA, etc.)
    company_patterns = [
        r"([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s]+(?:S\.A\.|CIA\.|LTDA\.|CIA|SOCIEDAD))",
        r"([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s]+(?:CONSTRUCTORA|EMPRESA))"
    ]
    
    for pattern in company_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        entities["companies"].extend(matches)
    
    # Location patterns (Ecuadorian provinces and cities)
    ecuador_locations = [
        "Guayas", "Pichincha", "Azuay", "Manabí", "El Oro", "Los Ríos",
        "Guayaquil", "Quito", "Cuenca", "Machala", "Ambato", "Manta",
        "Portoviejo", "Loja", "Riobamba", "Ibarra", "Esmeraldas",
        "Samborondón", "Daule", "Durán"
    ]
    
    for location in ecuador_locations:
        if location.lower() in text_content.lower():
            entities["locations"].append(location)
    
    # Remove duplicates
    for key in entities:
        entities[key] = list(set(entities[key]))
    
    return entities

async def prepare_document_for_analysis(file_path: str) -> Dict[str, Any]:
    """Prepare a document for comprehensive analysis."""
    try:
        # Extract text content
        text_content = await extract_text_from_file(file_path)
        
        # Analyze document
        document_info = {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "text_length": len(text_content),
            "extraction_timestamp": datetime.now().isoformat(),
            "text_content": text_content,
            "document_type": detect_document_type(text_content),
            "sections": extract_contract_sections(text_content),
            "financial_data": extract_financial_data(text_content),
            "entities": extract_entities(text_content)
        }
        
        return document_info
        
    except Exception as e:
        print(f"❌ Error preparing document for analysis: {e}")
        raise

def validate_tender_document(document_info: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that a document is suitable for tender analysis."""
    validation_result = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "document_quality": "good"
    }
    
    # Check text length
    text_length = document_info.get("text_length", 0)
    if text_length < 500:
        validation_result["errors"].append("Documento muy corto para análisis completo")
        validation_result["valid"] = False
    elif text_length < 1000:
        validation_result["warnings"].append("Documento corto, análisis puede ser limitado")
        validation_result["document_quality"] = "fair"
    
    # Check for key sections
    sections = document_info.get("sections", {})
    critical_sections = ["objeto", "monto", "plazo"]
    missing_sections = [section for section in critical_sections if section not in sections]
    
    if len(missing_sections) > 1:
        validation_result["errors"].append(f"Faltan secciones críticas: {', '.join(missing_sections)}")
        validation_result["valid"] = False
    elif missing_sections:
        validation_result["warnings"].append(f"Sección faltante: {', '.join(missing_sections)}")
    
    # Check for financial data
    financial_data = document_info.get("financial_data", {})
    if not financial_data.get("amounts_found"):
        validation_result["warnings"].append("No se detectaron montos financieros")
    
    # Check for entities (RUCs, companies)
    entities = document_info.get("entities", {})
    if not entities.get("rucs"):
        validation_result["warnings"].append("No se detectaron RUCs")
    if not entities.get("companies"):
        validation_result["warnings"].append("No se detectaron nombres de empresas")
    
    # Determine overall quality
    if validation_result["errors"]:
        validation_result["document_quality"] = "poor"
    elif len(validation_result["warnings"]) > 2:
        validation_result["document_quality"] = "fair"
    
    return validation_result

def clean_extracted_text(text: str) -> str:
    """Clean and normalize extracted text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers and headers/footers
    text = re.sub(r'Página \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\d+\s*de\s*\d+', '', text)
    
    # Normalize quotes and dashes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace('–', '-').replace('—', '-')
    
    # Remove extra newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def split_document_by_sections(text_content: str) -> List[Dict[str, str]]:
    """Split document into logical sections for processing."""
    sections = []
    
    # Common section headers
    section_markers = [
        r"PRIMERA\s*[-–]",
        r"SEGUNDA\s*[-–]", 
        r"TERCERA\s*[-–]",
        r"CUARTA\s*[-–]",
        r"QUINTA\s*[-–]",
        r"SEXTA\s*[-–]",
        r"SÉPTIMA\s*[-–]",
        r"OCTAVA\s*[-–]",
        r"NOVENA\s*[-–]",
        r"ANEXO\s+[IVX]+",
        r"FORMULARIO",
        r"ACTA\s+DE"
    ]
    
    # Find section boundaries
    boundaries = [0]
    
    for pattern in section_markers:
        matches = list(re.finditer(pattern, text_content, re.IGNORECASE))
        for match in matches:
            boundaries.append(match.start())
    
    boundaries.append(len(text_content))
    boundaries = sorted(set(boundaries))
    
    # Extract sections
    for i in range(len(boundaries) - 1):
        start = boundaries[i]
        end = boundaries[i + 1]
        section_text = text_content[start:end].strip()
        
        if section_text and len(section_text) > 50:  # Minimum section length
            # Try to identify section title
            first_line = section_text.split('\n')[0][:100]
            
            sections.append({
                "title": first_line.strip(),
                "content": section_text,
                "start_position": start,
                "end_position": end
            })
    
    return sections

async def batch_process_documents(file_paths: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
    """Process multiple documents concurrently."""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_single_document(file_path: str) -> Dict[str, Any]:
        async with semaphore:
            try:
                return await prepare_document_for_analysis(file_path)
            except Exception as e:
                return {
                    "file_path": file_path,
                    "error": str(e),
                    "success": False
                }
    
    tasks = [process_single_document(path) for path in file_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append({
                "file_path": file_paths[i],
                "error": str(result),
                "success": False
            })
        else:
            processed_results.append(result)
    
    return processed_results