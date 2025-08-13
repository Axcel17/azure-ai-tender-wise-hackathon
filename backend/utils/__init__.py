"""TenderWise Utilities Package - Helper functions and utilities."""

from .document_utils import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_file,
    detect_document_type,
    extract_contract_sections,
    extract_financial_data,
    extract_entities,
    prepare_document_for_analysis,
    validate_tender_document,
    clean_extracted_text,
    split_document_by_sections,
    batch_process_documents
)

from .file_utils import (
    validate_file_type,
    validate_file_size,
    generate_safe_filename,
    save_uploaded_file,
    get_file_info,
    create_session_directory,
    cleanup_old_files,
    get_available_space
)

from .response_utils import (
    create_api_response,
    handle_api_error,
    create_success_response,
    create_error_response,
    validate_required_fields,
    paginate_response,
    format_analysis_status,
    format_comparison_results
)

__all__ = [
    # Document utilities
    "extract_text_from_pdf",
    "extract_text_from_docx", 
    "extract_text_from_file",
    "detect_document_type",
    "extract_contract_sections",
    "extract_financial_data",
    "extract_entities",
    "prepare_document_for_analysis",
    "validate_tender_document",
    "clean_extracted_text",
    "split_document_by_sections",
    "batch_process_documents",
    
    # File utilities
    "validate_file_type",
    "validate_file_size",
    "generate_safe_filename",
    "save_uploaded_file",
    "get_file_info",
    "create_session_directory",
    "cleanup_old_files",
    "get_available_space",
    
    # Response utilities
    "create_api_response",
    "handle_api_error",
    "create_success_response",
    "create_error_response",
    "validate_required_fields",
    "paginate_response",
    "format_analysis_status",
    "format_comparison_results"
]

# Package metadata
__version__ = "1.0.0"
__author__ = "TenderWise Team"
__description__ = "Utility functions for tender document processing and API responses"