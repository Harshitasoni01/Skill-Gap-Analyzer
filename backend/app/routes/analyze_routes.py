from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.schemas import AnalysisResponse
from app.services.analyzer import analyze_resume
from app.services.gemini_client import AIServiceError
from app.services.resume_parser import extract_text

router = APIRouter(prefix="/api", tags=["Analyzer"])

MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB
MIN_JD_CHARS = 40


async def read_upload_as_text(upload: UploadFile, label: str) -> str:
    file_bytes = await upload.read()

    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail=f"The {label} file is larger than 5 MB.")

    try:
        text = extract_text(upload.filename, file_bytes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read the {label} file. It may be corrupted or password protected.",
        )

    if not text:
        raise HTTPException(
            status_code=422,
            detail=f"No readable text found in the {label}. If it is a scanned PDF, "
            "please upload a text-based PDF or a DOCX.",
        )
    return text


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    resume: UploadFile = File(...),
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
):
    resume_text = await read_upload_as_text(resume, "resume")

    jd = (jd_text or "").strip()
    if not jd and jd_file is not None and jd_file.filename:
        jd = await read_upload_as_text(jd_file, "job description")

    if len(jd) < MIN_JD_CHARS:
        raise HTTPException(
            status_code=422,
            detail="Please provide a job description (paste it or upload a file).",
        )

    try:
        return await run_in_threadpool(analyze_resume, resume_text, jd)
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)
