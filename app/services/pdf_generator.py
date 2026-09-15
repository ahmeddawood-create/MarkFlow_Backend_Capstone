import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.assignment import Assignment
from app.models.user import User


def generate_evaluation_pdf(
    evaluation: Evaluation,
    submission: Submission,
    assignment: Assignment,
    student: User
) -> io.BytesIO:
    """
    Generate a professional single-page PDF assessment grade card using ReportLab.
    Returns an in-memory BytesIO stream for instant download.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b")
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    feedback_style = ParagraphStyle(
        'FeedbackBox',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )

    # Header
    story.append(Paragraph("<b>MarkFlow</b> | Student Assessment Grade Card", title_style))
    story.append(Paragraph(f"Deterministic AI Evaluation Pipeline · Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3b82f6"), spaceAfter=12))

    # Meta Information Table
    percentage = (evaluation.score_awarded / evaluation.max_possible_score * 100) if evaluation.max_possible_score > 0 else 0
    meta_data = [
        [
            Paragraph(f"<b>Student:</b> {student.full_name or student.email}", body_style),
            Paragraph(f"<b>Assignment:</b> {assignment.title}", body_style),
        ],
        [
            Paragraph(f"<b>Student ID:</b> #{student.id}", body_style),
            Paragraph(f"<b>Submitted:</b> {submission.submitted_at.strftime('%Y-%m-%d %H:%M')}", body_style),
        ],
        [
            Paragraph(f"<b>Grade:</b> <font color='#2563eb'><b>{evaluation.score_awarded:.1f} / {evaluation.max_possible_score:.1f} ({percentage:.1f}%)</b></font>", body_style),
            Paragraph(f"<b>Evaluation Latency:</b> {evaluation.latency_seconds:.2f}s", body_style),
        ]
    ]

    meta_table = Table(meta_data, colWidths=[260, 280])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Rubric Step Breakdown Table
    story.append(Paragraph("<b>Step-by-Step Mark Scheme Breakdown</b>", section_heading))

    rubric_rows = [
        [
            Paragraph("<b>Step #</b>", body_style),
            Paragraph("<b>Awarded / Max</b>", body_style),
            Paragraph("<b>Marker Feedback & Observations</b>", body_style),
        ]
    ]

    for step in evaluation.step_breakdown:
        step_num = step.get("step", "-")
        awarded = step.get("awarded", 0.0)
        max_m = step.get("max", 0.0)
        notes = step.get("notes", "")

        rubric_rows.append([
            Paragraph(f"Step {step_num}", body_style),
            Paragraph(f"<b>{awarded:.1f}</b> / {max_m:.1f}", body_style),
            Paragraph(notes, body_style),
        ])

    rubric_table = Table(rubric_rows, colWidths=[60, 95, 385])
    rubric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(rubric_table)
    story.append(Spacer(1, 14))

    # Overall Qualitative Feedback
    story.append(Paragraph("<b>Overall Assessment Feedback</b>", section_heading))
    feedback_p = Paragraph(evaluation.overall_feedback or "No overall notes recorded.", feedback_style)
    feedback_table = Table([[feedback_p]], colWidths=[540])
    feedback_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ('BOX', (0, 0), (-1, -1), 1.0, colors.HexColor("#bfdbfe")),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(feedback_table)
    story.append(Spacer(1, 14))

    # 10x Metrics Footer
    metrics_text = (
        f"<b>Audit & Economics:</b> Tokens: {evaluation.prompt_tokens} prompt / {evaluation.completion_tokens} completion · "
        f"Estimated Cost: ${evaluation.estimated_cost_usd:.4f} · "
        f"Pipeline Speed: {evaluation.latency_seconds:.2f}s (vs. ~900s manual grading average)"
    )
    story.append(Paragraph(metrics_text, subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
