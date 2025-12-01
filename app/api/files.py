"""
File upload and management endpoints.
"""
import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.config import settings

router = APIRouter()

# Directory for uploaded files
UPLOAD_DIR = Path(settings.uploads_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/api/upload", tags=["files"])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a Markdown file for exam generation.

    Args:
        file: Markdown file (.md)

    Returns:
        File information and path
    """
    # Validate file extension
    if not file.filename.endswith('.md'):
        raise HTTPException(
            status_code=400,
            detail="Only .md (Markdown) files are allowed"
        )

    # Save file
    file_path = UPLOAD_DIR / file.filename
    try:
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        return {
            "filename": file.filename,
            "path": str(file_path),
            "size": len(content),
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )


@router.get("/api/files", tags=["files"])
async def list_files():
    """
    List all uploaded Markdown files.

    Returns:
        List of uploaded files with metadata
    """
    files = []
    for file_path in UPLOAD_DIR.glob("*.md"):
        stat = file_path.stat()
        files.append({
            "filename": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "modified": stat.st_mtime
        })

    return {"files": files, "count": len(files)}


@router.get("/api/files/{filename}", tags=["files"])
async def get_file_content(filename: str):
    """
    Get content of an uploaded file.

    Args:
        filename: Name of the file

    Returns:
        File content
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found"
        )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "filename": filename,
            "content": content,
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read file: {str(e)}"
        )


@router.get("/api/exams", tags=["exams"])
async def list_exams():
    """
    List all generated exams.

    Returns:
        List of exams with metadata
    """
    exams = []
    out_dir = Path(settings.output_dir)

    for exam_file in out_dir.glob("exam_*.json"):
        stat = exam_file.stat()
        exam_id = exam_file.stem.replace("exam_", "")

        exams.append({
            "exam_id": exam_id,
            "filename": exam_file.name,
            "path": str(exam_file),
            "size": stat.st_size,
            "created": stat.st_mtime
        })

    return {"exams": exams, "count": len(exams)}


@router.get("/api/exams/{exam_id}", tags=["exams"])
async def get_exam(exam_id: str):
    """
    Get a specific exam by ID.

    Args:
        exam_id: Exam identifier

    Returns:
        Full exam data
    """
    import json

    exam_file = Path(settings.output_dir) / f"exam_{exam_id}.json"

    if not exam_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Exam '{exam_id}' not found"
        )

    try:
        with open(exam_file, 'r', encoding='utf-8') as f:
            exam_data = json.load(f)

        return exam_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load exam: {str(e)}"
        )
