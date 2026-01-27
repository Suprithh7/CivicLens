from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.schemas.policy import PolicyUploadResponse
from datetime import datetime
import os
import uuid
from pathlib import Path

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = Path("uploads/policies")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_pdf(file: UploadFile) -> None:
    """Validate uploaded file is a PDF and within size limits."""
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only PDF files are allowed. Got: {file_ext}"
        )
    
    # Check content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type. Expected 'application/pdf', got '{file.content_type}'"
        )


@router.post(
    "/upload",
    response_model=PolicyUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Policy Document",
    description="Upload a policy document (PDF only). Maximum file size: 10MB."
)
async def upload_policy(
    file: UploadFile = File(..., description="PDF file to upload")
) -> PolicyUploadResponse:
    """
    Upload a policy document.
    
    Args:
        file: PDF file to upload
        
    Returns:
        PolicyUploadResponse: Upload confirmation with file metadata
        
    Raises:
        HTTPException: If file validation fails or upload errors occur
    """
    
    # Validate file
    validate_pdf(file)
    
    # Generate unique ID and filename
    policy_id = f"pol_{uuid.uuid4().hex[:12]}"
    file_ext = os.path.splitext(file.filename)[1]
    stored_filename = f"{policy_id}{file_ext}"
    file_path = UPLOAD_DIR / stored_filename
    
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create response
        return PolicyUploadResponse(
            id=policy_id,
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type,
            upload_timestamp=datetime.utcnow(),
            storage_path=str(file_path.relative_to(Path.cwd())),
            status="uploaded"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if it was created
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    finally:
        await file.close()


@router.get(
    "/list",
    summary="List Uploaded Policies",
    description="Get a list of all uploaded policy documents."
)
async def list_policies():
    """
    List all uploaded policy documents.
    
    Returns:
        List of policy metadata
    """
    policies = []
    
    if UPLOAD_DIR.exists():
        for file_path in UPLOAD_DIR.glob("*.pdf"):
            stat = file_path.stat()
            policies.append({
                "id": file_path.stem,
                "filename": file_path.name,
                "file_size": stat.st_size,
                "upload_timestamp": datetime.fromtimestamp(stat.st_mtime),
                "storage_path": str(file_path.relative_to(Path.cwd()))
            })
    
    return {"policies": policies, "count": len(policies)}
