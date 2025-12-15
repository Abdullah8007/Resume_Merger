from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List
import uvicorn
import os

from services.parser import ResumeParser
from services.merger import ResumeMerger
from services.exporter import ResumeExporter
from models.schemas import MergeRequest, MergeResponse, ParsedResume

app = FastAPI(title="Resume Merger API", version="1.0.0")

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
parser = ResumeParser()
merger = ResumeMerger()
exporter = ResumeExporter()

# Create upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
async def root():
    return {
        "message": "Resume Merger API",
        "version": "1.0.0",
        "endpoints": ["/upload", "/parse", "/merge", "/export"]
    }


@app.post("/api/upload")
async def upload_resumes(files: List[UploadFile] = File(...)):
    """Upload and parse multiple resumes"""
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload at least 2 resumes")
    
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 resumes allowed")
    
    parsed_resumes = []
    
    for file in files:
        # Validate file type
        if not file.filename.endswith(('.pdf', '.docx')):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}. Only PDF and DOCX are supported."
            )
        
        # Save file temporarily
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse resume
        try:
            parsed_data = parser.parse_resume(file_path)
            parsed_resumes.append({
                "filename": file.filename,
                "data": parsed_data
            })
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error parsing {file.filename}: {str(e)}"
            )
        finally:
            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
    
    return {
        "success": True,
        "count": len(parsed_resumes),
        "resumes": parsed_resumes
    }


@app.post("/api/merge")
async def merge_resumes(request: MergeRequest):
    """Merge multiple parsed resumes into one"""
    if len(request.resumes) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 resumes to merge")
    
    try:
        merged_resume = merger.merge(request.resumes, request.settings)
        
        return MergeResponse(
            success=True,
            merged_resume=merged_resume
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging resumes: {str(e)}")


@app.post("/api/export/{format}")
async def export_resume(format: str, resume_data: dict):
    """Export merged resume as PDF or DOCX"""
    if format not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Format must be 'pdf' or 'docx'")
    
    try:
        output_path = exporter.export(resume_data, format)
        
        return FileResponse(
            output_path,
            media_type="application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"merged_resume.{format}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting resume: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
