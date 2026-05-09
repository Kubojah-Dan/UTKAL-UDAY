"""
Certificate generation API.
Uses fpdf2 (pure Python, no system dependencies) to generate PDF certificates.
Install: pip install fpdf2
"""
import logging
import os
from datetime import datetime
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.core.auth import get_current_user
from app.core.leaderboard_service import get_my_rank

router = APIRouter()
logger = logging.getLogger("certificates")

PLATFORM_NAME = "Utkal Uday"
PLATFORM_TAGLINE = "AI-Powered Learning for Rural India"


def _generate_pdf_certificate(
    student_name: str,
    grade: int,
    school: str,
    rank: int,
    scope: str,
    month_year: str,
    total_xp: int,
) -> bytes:
    """Generate a PDF certificate using fpdf2."""
    try:
        from fpdf import FPDF

        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_auto_page_break(auto=False)

        W, H = 297, 210  # A4 landscape

        # ── Background gradient effect (filled rect layers) ─────────────────
        pdf.set_fill_color(15, 40, 80)
        pdf.rect(0, 0, W, H, "F")

        pdf.set_fill_color(10, 30, 65)
        pdf.rect(0, H - 40, W, 40, "F")

        # ── Gold border ──────────────────────────────────────────────────────
        pdf.set_draw_color(212, 175, 55)
        pdf.set_line_width(3)
        pdf.rect(10, 10, W - 20, H - 20)
        pdf.set_line_width(1)
        pdf.rect(13, 13, W - 26, H - 26)

        # ── Platform name ────────────────────────────────────────────────────
        pdf.set_text_color(212, 175, 55)
        pdf.set_font("Helvetica", "B", 28)
        pdf.set_xy(0, 20)
        pdf.cell(W, 12, PLATFORM_NAME, align="C")

        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(180, 200, 220)
        pdf.set_xy(0, 34)
        pdf.cell(W, 6, PLATFORM_TAGLINE, align="C")

        # ── Certificate title ─────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(0, 50)
        pdf.cell(W, 10, "CERTIFICATE OF ACHIEVEMENT", align="C")

        # ── Decorative line ───────────────────────────────────────────────────
        pdf.set_draw_color(212, 175, 55)
        pdf.set_line_width(0.8)
        pdf.line(60, 63, W - 60, 63)

        # ── This is to certify ────────────────────────────────────────────────
        pdf.set_font("Helvetica", "I", 12)
        pdf.set_text_color(180, 200, 220)
        pdf.set_xy(0, 67)
        pdf.cell(W, 8, "This is to certify that", align="C")

        # ── Student name ──────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 32)
        pdf.set_text_color(212, 175, 55)
        pdf.set_xy(0, 77)
        pdf.cell(W, 16, student_name.upper(), align="C")

        # ── Achievement text ──────────────────────────────────────────────────
        pdf.set_font("Helvetica", "", 13)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(0, 96)

        scope_label = {"school": "School", "class": "Class", "district": "District", "state": "State"}.get(scope, scope.capitalize())
        rank_suffix = {1: "st", 2: "nd", 3: "rd"}.get(rank, "th")

        pdf.cell(W, 8, f"has achieved {rank}{rank_suffix} Rank on the {scope_label} Leaderboard", align="C")

        pdf.set_xy(0, 106)
        pdf.cell(W, 8, f"Grade {grade} · {school}", align="C")

        # ── XP and month ──────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(212, 175, 55)
        pdf.set_xy(0, 118)
        pdf.cell(W, 8, f"Total XP Earned: {total_xp:,}  ·  {month_year}", align="C")

        # ── Decorative line ───────────────────────────────────────────────────
        pdf.set_draw_color(212, 175, 55)
        pdf.line(60, 130, W - 60, 130)

        # ── Footer ────────────────────────────────────────────────────────────
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(120, 160, 200)
        pdf.set_xy(0, 135)
        pdf.cell(W, 6, "Empowering rural students through AI-adaptive learning", align="C")

        pdf.set_xy(0, 143)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(W, 5, f"Issued by {PLATFORM_NAME} · {datetime.utcnow().strftime('%d %B %Y')}", align="C")

        return pdf.output()

    except ImportError:
        logger.error("fpdf2 not installed — run: pip install fpdf2")
        raise HTTPException(status_code=500, detail="Certificate generation requires fpdf2. Run: pip install fpdf2")


@router.get("/certificates/generate/{student_id}")
async def generate_certificate(
    student_id: str,
    scope:      str           = "school",
    grade:      Optional[int] = None,
    user=Depends(get_current_user),
):
    """Generate and return a PDF certificate for a student."""
    # Only the student themselves or a teacher can download
    caller_id = str(user.get("user_id") or user.get("id") or "")
    if caller_id != student_id and user.get("role") not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch student info from leaderboard
    rank_info = await get_my_rank(
        student_id=student_id,
        scope=scope,
        grade=grade or user.get("class_grade"),
    )

    if not rank_info.get("found"):
        raise HTTPException(status_code=404, detail="Student not found in leaderboard")

    rank = rank_info.get("rank", 0)
    if rank > 3:
        raise HTTPException(
            status_code=403,
            detail=f"Certificates are issued for Top 3 students. Your current rank is #{rank}."
        )

    # Fetch student profile
    try:
        from app.core.database import async_db
        lb_col = async_db["student_leaderboard"]
        student = await lb_col.find_one({"student_id": student_id})
        student = student or {}
    except Exception:
        student = {}

    name     = student.get("name", student_id)
    school   = student.get("school", "")
    grade_n  = grade or student.get("grade", 0)
    total_xp = rank_info.get("total_xp", 0)
    month_year = datetime.utcnow().strftime("%B %Y")

    pdf_bytes = _generate_pdf_certificate(
        student_name=name,
        grade=grade_n,
        school=school,
        rank=rank,
        scope=scope,
        month_year=month_year,
        total_xp=total_xp,
    )

    safe_name = name.replace(" ", "_")
    filename  = f"UtkalUday_Certificate_{safe_name}_{month_year.replace(' ','_')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
