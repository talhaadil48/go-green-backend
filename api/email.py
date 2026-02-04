from fastapi import APIRouter, HTTPException, Request , Depends
from fastapi import FastAPI, UploadFile, Form, HTTPException, File
from fastapi.responses import JSONResponse
from email.message import EmailMessage
import smtplib
import os
import re
from dotenv import load_dotenv
from pathlib import Path


# resolve project root and load .env.local
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env.local"

load_dotenv(dotenv_path=ENV_PATH)


router = APIRouter(tags=["Email"] )

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_SECURE = os.getenv("EMAIL_SECURE", "true") != "false"


if not EMAIL_USER or not EMAIL_PASS:
    print("Missing EMAIL_USER or EMAIL_PASS in environment variables")


def safe_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)


@router.post("/send")
async def send_documents(
    email: str = Form(...),
    subject: str = Form("New Document Submission"),
    message: str = Form(""),
    claimId: str = Form("unknown"),
    fileCount: int = Form(...),
    files: list[UploadFile] = File(...)
):
    if fileCount == 0 or not email:
        raise HTTPException(status_code=400, detail="At least one file and email required")

    attachments = []
    for i, file in enumerate(files):
        if file.filename and file.filename.strip():
            content = await file.read()
            attachments.append({
                "filename": safe_filename(file.filename),
                "content": content,
                "content_type": file.content_type or "application/octet-stream"
            })

    if not attachments:
        raise HTTPException(status_code=400, detail="No valid files received")

    # Compose email
    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = email
    msg["Reply-To"] = email
    msg["Subject"] = f"{subject} – Claim #{claimId}"
    body_text = f"""
New document submission received!

From: {email}
Claim ID: {claimId}

Message:
{message or '(no message provided)'}

Attachments included: {', '.join(att['filename'] for att in attachments)}
"""
    msg.set_content(body_text)

    for att in attachments:
        msg.add_attachment(
            att["content"],
            maintype=att["content_type"].split("/")[0],
            subtype=att["content_type"].split("/")[1],
            filename=att["filename"]
        )

    try:
        if EMAIL_SECURE:
            server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
        else:
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        return JSONResponse({
            "success": True,
            "message": f"Sent {len(attachments)} file(s) successfully to {email}",
            "sent_files": [att["filename"] for att in attachments]
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": "Failed to send email",
            "error": str(e)
        }, status_code=500)
