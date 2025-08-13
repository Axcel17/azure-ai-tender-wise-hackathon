"""API response utilities for TenderWise."""

from typing import Any, Dict, Optional, List
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import traceback

def create_api_response(
    success: bool = True,
    message: str = "",
    data: Optional[Any] = None,
    error: Optional[str] = None,
    status_code: int = 200
) -> Dict[str, Any]:
    """Create standardized API response."""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    if error is not None:
        response["error"] = error
    
    return response

def handle_api_error(
    exception: Exception,
    message: str = "An error occurred",
    include_traceback: bool = False
) -> JSONResponse:
    """Handle API errors consistently."""
    error_details = str(exception)
    
    if include_traceback:
        error_details = {
            "message": str(exception),
            "traceback": traceback.format_exc()
        }
    
    # Determine status code based on exception type
    status_code = 500
    if isinstance(exception, FileNotFoundError):
        status_code = 404
    elif isinstance(exception, ValueError):
        status_code = 400
    elif isinstance(exception, PermissionError):
        status_code = 403
    
    response_data = create_api_response(
        success=False,
        message=message,
        error=error_details,
        status_code=status_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )

def create_success_response(
    message: str,
    data: Optional[Any] = None
) -> Dict[str, Any]:
    """Create success response."""
    return create_api_response(
        success=True,
        message=message,
        data=data
    )

def create_error_response(
    message: str,
    error: Optional[str] = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """Create error response."""
    return create_api_response(
        success=False,
        message=message,
        error=error,
        status_code=status_code
    )

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Optional[str]:
    """Validate that required fields are present in data."""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    
    return None

def paginate_response(
    data: list,
    page: int = 1,
    per_page: int = 20,
    total_count: Optional[int] = None
) -> Dict[str, Any]:
    """Create paginated response."""
    if total_count is None:
        total_count = len(data)
    
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    
    paginated_data = data[start_index:end_index]
    
    total_pages = (total_count + per_page - 1) // per_page
    
    pagination_info = {
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    return {
        "data": paginated_data,
        "pagination": pagination_info
    }

def format_analysis_status(status_info: Dict[str, Any]) -> Dict[str, Any]:
    """Format analysis status for API response."""
    formatted_status = {
        "analysis_id": status_info.get("analysis_id"),
        "status": status_info.get("status", "unknown"),
        "progress": {
            "current_stage": status_info.get("current_stage"),
            "completion_percentage": _calculate_completion_percentage(status_info)
        },
        "timestamps": {
            "started_at": status_info.get("start_time"),
            "updated_at": status_info.get("updated_at", datetime.now().isoformat()),
            "estimated_completion": _estimate_completion_time(status_info)
        },
        "results_available": bool(status_info.get("results"))
    }
    
    if status_info.get("error"):
        formatted_status["error"] = status_info["error"]
    
    return formatted_status

def _calculate_completion_percentage(status_info: Dict[str, Any]) -> int:
    """Calculate completion percentage based on current stage."""
    stage_percentages = {
        "document_extraction": 20,
        "compliance_validation": 40,
        "ruc_validation": 60,
        "risk_assessment": 80,
        "report_generation": 95,
        "completed": 100,
        "failed": 0
    }
    
    current_stage = status_info.get("current_stage", "")
    status = status_info.get("status", "")
    
    if status == "completed":
        return 100
    elif status == "failed":
        return 0
    
    return stage_percentages.get(current_stage, 0)

def _estimate_completion_time(status_info: Dict[str, Any]) -> Optional[str]:
    """Estimate completion time based on current progress."""
    start_time = status_info.get("start_time")
    current_stage = status_info.get("current_stage")
    
    if not start_time or not current_stage:
        return None
    
    # Rough estimates for each stage (in minutes)
    stage_durations = {
        "document_extraction": 2,
        "compliance_validation": 3,
        "ruc_validation": 5,
        "risk_assessment": 4,
        "report_generation": 3
    }
    
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        elapsed_minutes = (datetime.now() - start_dt).total_seconds() / 60
        
        remaining_minutes = stage_durations.get(current_stage, 2)
        estimated_end = datetime.now().timestamp() + (remaining_minutes * 60)
        
        return datetime.fromtimestamp(estimated_end).isoformat()
    except:
        return None

def format_comparison_results(comparison_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format comparison results for API response."""
    return {
        "comparison_id": comparison_data.get("comparison_id"),
        "proposals_count": comparison_data.get("proposals_analyzed", 0),
        "winner": _extract_winner_info(comparison_data),
        "rankings": _format_rankings(comparison_data),
        "summary": _create_comparison_summary(comparison_data),
        "detailed_analysis": comparison_data.get("comparison_matrix"),
        "recommendations": comparison_data.get("recommendations")
    }

def _extract_winner_info(comparison_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Extract winner information from comparison results."""
    # This would parse the comparison results to identify the winner
    # Implementation depends on the structure of comparison_matrix
    return None

def _format_rankings(comparison_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format proposal rankings."""
    # This would extract and format the ranking information
    # Implementation depends on the structure of comparison_matrix
    return []

def _create_comparison_summary(comparison_data: Dict[str, Any]) -> Dict[str, str]:
    """Create a summary of the comparison."""
    return {
        "recommendation": "Análisis completo disponible en resultados detallados",
        "key_differentiators": "Ver matriz de comparación para factores clave",
        "confidence_level": "Alta"
    }