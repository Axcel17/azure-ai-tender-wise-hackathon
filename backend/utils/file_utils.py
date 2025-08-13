"""File handling utilities for TenderWise."""

import os
import uuid
import aiofiles
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import UploadFile
import mimetypes

def validate_file_type(filename: str, allowed_types: List[str] = None) -> bool:
    """Validate if file type is allowed."""
    if allowed_types is None:
        allowed_types = ['.pdf', '.docx', '.doc']
    
    file_ext = Path(filename).suffix.lower()
    return file_ext in allowed_types

def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
    """Validate if file size is within limits."""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def generate_safe_filename(original_filename: str, session_id: str) -> str:
    """Generate a safe filename for storage."""
    # Get file extension
    file_ext = Path(original_filename).suffix.lower()
    
    # Create safe base name
    base_name = Path(original_filename).stem
    safe_base = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_base = safe_base[:50]  # Limit length
    
    # Add unique identifier
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return f"{safe_base}_{timestamp}_{unique_id}{file_ext}"

async def save_uploaded_file(file: UploadFile, session_id: str, upload_dir: str = "uploads") -> str:
    """Save uploaded file to disk."""
    # Create upload directory if it doesn't exist
    session_dir = os.path.join(upload_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # Generate safe filename
    safe_filename = generate_safe_filename(file.filename, session_id)
    file_path = os.path.join(session_dir, safe_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    return file_path

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get comprehensive file information."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat_info = os.stat(file_path)
    
    return {
        "file_path": file_path,
        "filename": os.path.basename(file_path),
        "file_size": stat_info.st_size,
        "file_size_mb": round(stat_info.st_size / (1024 * 1024), 2),
        "creation_time": datetime.fromtimestamp(stat_info.st_ctime),
        "modification_time": datetime.fromtimestamp(stat_info.st_mtime),
        "file_extension": Path(file_path).suffix.lower(),
        "mime_type": mimetypes.guess_type(file_path)[0]
    }

def create_session_directory(session_id: str, base_dir: str = "uploads") -> str:
    """Create directory for session files."""
    session_dir = os.path.join(base_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    return session_dir

def cleanup_old_files(directory: str, days_old: int = 7) -> int:
    """Clean up files older than specified days."""
    if not os.path.exists(directory):
        return 0
    
    deleted_count = 0
    cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
            except (OSError, IOError):
                continue  # Skip files we can't delete
    
    return deleted_count

def get_available_space(directory: str) -> Dict[str, float]:
    """Get available disk space information."""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    stat_info = os.statvfs(directory)
    
    # Calculate space in bytes
    total_space = stat_info.f_frsize * stat_info.f_blocks
    available_space = stat_info.f_frsize * stat_info.f_available
    used_space = total_space - available_space
    
    return {
        "total_gb": round(total_space / (1024**3), 2),
        "available_gb": round(available_space / (1024**3), 2),
        "used_gb": round(used_space / (1024**3), 2),
        "usage_percent": round((used_space / total_space) * 100, 2)
    }