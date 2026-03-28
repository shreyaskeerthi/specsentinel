"""Document upload and management endpoints."""

from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, CurrentUser, CurrentOrg
from app.core.config import settings
from app.models.project import Project
from app.models.document import Document, DocumentStatus
from app.models.subscription import Subscription
from app.services.storage import storage_service
from app.services.analysis_pipeline import analysis_pipeline
from app.services.export import export_service
from app.schemas.document import DocumentRead, DocumentUploadResponse
from app.schemas.analysis import SpecExtraction, RiskReport, DivisionData, AnalysisResultRead
from app.models.analysis import AnalysisResult

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    *,
    db: DbSession,
    organization: CurrentOrg,
    current_user: CurrentUser,
    project_id: UUID = Form(...),
    file: UploadFile = File(...),
) -> dict:
    """
    Upload a PDF document for analysis.
    Runs the analysis pipeline synchronously and returns results.
    """
    # Verify project belongs to organization
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Check file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed ({settings.MAX_FILE_SIZE_MB}MB)",
        )

    # Check document limit
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization.id
    ).first()

    if subscription and subscription.plan:
        max_docs = subscription.plan.max_documents_per_month
        if max_docs > 0 and subscription.documents_analyzed_this_month >= max_docs:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Monthly document limit ({max_docs}) reached. Please upgrade your plan.",
            )

    # Save file
    filename, file_path = await storage_service.save_file(
        file_content=content,
        organization_id=organization.id,
        original_filename=file.filename,
    )

    # Create document record
    document = Document(
        filename=filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type="application/pdf",
        status=DocumentStatus.PENDING,
        project_id=project_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Run analysis pipeline
    try:
        analysis_result = analysis_pipeline.process_document(db, document)

        # Update usage counter
        if subscription:
            subscription.documents_analyzed_this_month += 1
            db.commit()

        # Format response
        doc_read = DocumentRead.model_validate(document)

        analysis_read = AnalysisResultRead(
            id=analysis_result.id,
            document_id=analysis_result.document_id,
            extraction=SpecExtraction(**analysis_result.extraction_data),
            risk_report=RiskReport(**analysis_result.risk_report),
            division_data=DivisionData(**analysis_result.division_data) if analysis_result.division_data else None,
            created_at=analysis_result.created_at,
            updated_at=analysis_result.updated_at,
        )

        return {"document": doc_read, "analysis": analysis_read}

    except Exception as e:
        # Analysis failed but document was saved
        db.refresh(document)
        return {
            "document": DocumentRead.model_validate(document),
            "analysis": None,
            "error": str(e),
        }


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    *,
    db: DbSession,
    organization: CurrentOrg,
    document_id: UUID,
) -> Document:
    """Get a specific document by ID."""
    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.organization_id == organization.id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    *,
    db: DbSession,
    organization: CurrentOrg,
    document_id: UUID,
):
    """Delete a document and its analysis."""
    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.organization_id == organization.id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Delete file from storage
    await storage_service.delete_file(document.file_path)

    # Delete document (cascade deletes analysis)
    db.delete(document)
    db.commit()


@router.get("/{document_id}/download")
def download_document(
    *,
    db: DbSession,
    organization: CurrentOrg,
    document_id: UUID,
):
    """Download the original PDF document."""
    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.organization_id == organization.id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Check if file exists
    import os
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on server",
        )

    return FileResponse(
        path=document.file_path,
        filename=document.original_filename,
        media_type="application/pdf",
    )


@router.get("/{document_id}/download-highlighted")
def download_highlighted_document(
    *,
    db: DbSession,
    organization: CurrentOrg,
    document_id: UUID,
    search_text: str | None = None,
    page: int | None = None,
):
    """
    Download PDF with text highlighted.
    Uses PyMuPDF to add yellow highlight annotations.
    """
    import os
    import tempfile
    import fitz  # PyMuPDF

    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.organization_id == organization.id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on server",
        )

    # If no search text, return original
    if not search_text:
        return FileResponse(
            path=document.file_path,
            filename=document.original_filename,
            media_type="application/pdf",
        )

    try:
        import re

        # Open PDF with PyMuPDF
        pdf_doc = fitz.open(document.file_path)

        # Determine pages to search
        if page and 1 <= page <= len(pdf_doc):
            pages_to_search = [page - 1]  # Convert to 0-indexed
        else:
            pages_to_search = range(len(pdf_doc))

        def normalize_text(text: str) -> str:
            """Normalize text for comparison - collapse whitespace, lowercase."""
            return re.sub(r'\s+', ' ', text.lower().strip())

        def highlight_text_on_page(pdf_page, text_to_find: str) -> int:
            """Try multiple strategies to highlight text. Returns count of highlights added."""
            count = 0

            # Strategy 1: Direct search (PyMuPDF handles some whitespace)
            instances = pdf_page.search_for(text_to_find)
            for inst in instances:
                highlight = pdf_page.add_highlight_annot(inst)
                highlight.set_colors(stroke=(1, 1, 0))  # Yellow
                highlight.update()
                count += 1

            if count > 0:
                return count

            # Strategy 2: Try with collapsed whitespace
            collapsed = re.sub(r'\s+', ' ', text_to_find.strip())
            if collapsed != text_to_find:
                instances = pdf_page.search_for(collapsed)
                for inst in instances:
                    highlight = pdf_page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=(1, 1, 0))
                    highlight.update()
                    count += 1

            if count > 0:
                return count

            # Strategy 3: Split by newlines/periods and highlight each meaningful segment
            segments = re.split(r'[\n.!?;:]', text_to_find)
            for seg in segments:
                seg = seg.strip()
                if len(seg) > 8:  # Only meaningful segments
                    instances = pdf_page.search_for(seg)
                    for inst in instances:
                        highlight = pdf_page.add_highlight_annot(inst)
                        highlight.set_colors(stroke=(1, 1, 0))
                        highlight.update()
                        count += 1

            if count > 0:
                return count

            # Strategy 4: Try word-by-word for longer phrases (highlight key words)
            words = text_to_find.split()
            if len(words) > 3:
                # Try 3-word chunks
                for i in range(len(words) - 2):
                    chunk = ' '.join(words[i:i+3])
                    if len(chunk) > 10:
                        instances = pdf_page.search_for(chunk)
                        for inst in instances:
                            highlight = pdf_page.add_highlight_annot(inst)
                            highlight.set_colors(stroke=(1, 1, 0))
                            highlight.update()
                            count += 1

            return count

        # Search and highlight
        highlight_count = 0
        for page_num in pages_to_search:
            pdf_page = pdf_doc[page_num]
            page_text = pdf_page.get_text()

            # Normalize both texts for comparison
            search_normalized = normalize_text(search_text)
            page_normalized = normalize_text(page_text)

            # Find approximate location in normalized text
            match_idx = page_normalized.find(search_normalized)

            if match_idx != -1:
                # Find the original text position (approximate)
                orig_idx = 0
                norm_idx = 0

                # Find where in original text our match starts
                while norm_idx < match_idx and orig_idx < len(page_text):
                    if page_text[orig_idx].isspace():
                        # Skip extra whitespace in original
                        while orig_idx < len(page_text) - 1 and page_text[orig_idx + 1].isspace():
                            orig_idx += 1
                    orig_idx += 1
                    norm_idx += 1

                start_idx = max(0, orig_idx)

                # Find the START of the sentence (go backwards up to 400 chars)
                sentence_start = start_idx
                for i in range(start_idx - 1, max(0, start_idx - 400), -1):
                    char = page_text[i]
                    if char in '.!?:':
                        sentence_start = i + 1
                        break
                else:
                    sentence_start = max(0, start_idx - 50)  # Just go back a bit if no boundary

                # Skip leading whitespace
                while sentence_start < len(page_text) and page_text[sentence_start] in ' \n\t\r':
                    sentence_start += 1

                # Find the END of the sentence - MUST find a period/terminator
                # Start from where the search text would end
                search_end_approx = start_idx + len(search_text)
                sentence_end = len(page_text)  # Default to end of page

                # Look for sentence terminator up to 600 chars forward
                for i in range(search_end_approx, min(len(page_text), search_end_approx + 600)):
                    char = page_text[i]
                    if char in '.!?':
                        # Make sure it's actually end of sentence (not abbreviation like "Dr." or "Inc.")
                        # Check if followed by space and capital or end
                        if i + 1 >= len(page_text):
                            sentence_end = i + 1
                            break
                        next_char = page_text[i + 1] if i + 1 < len(page_text) else ' '
                        if next_char in ' \n\t\r':
                            # Check for capital letter after space (real sentence end)
                            j = i + 1
                            while j < len(page_text) and page_text[j] in ' \n\t\r':
                                j += 1
                            if j >= len(page_text) or page_text[j].isupper() or page_text[j].isdigit():
                                sentence_end = i + 1
                                break
                            # Also accept if we're at a clear break (double newline)
                            if '\n\n' in page_text[i:i+5]:
                                sentence_end = i + 1
                                break

                # Get the full sentence text to highlight
                full_sentence = page_text[sentence_start:sentence_end].strip()

                # Highlight the full sentence using multiple strategies
                highlight_count += highlight_text_on_page(pdf_page, full_sentence)

                # Also try to highlight the original search text directly if nothing worked
                if highlight_count == 0:
                    highlight_count += highlight_text_on_page(pdf_page, search_text)
            else:
                # Fallback: try direct search with multiple strategies
                highlight_count += highlight_text_on_page(pdf_page, search_text)

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_doc.save(temp_file.name)
        pdf_doc.close()

        # Return highlighted PDF
        from fastapi.responses import Response
        with open(temp_file.name, "rb") as f:
            pdf_content = f.read()

        # Clean up temp file
        os.unlink(temp_file.name)

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{document.original_filename}"',
                "X-Highlight-Count": str(highlight_count),
            }
        )

    except Exception as e:
        # If highlighting fails, return original
        return FileResponse(
            path=document.file_path,
            filename=document.original_filename,
            media_type="application/pdf",
        )


@router.get("/{document_id}/export-pdf")
def export_risk_report_pdf(
    *,
    db: DbSession,
    organization: CurrentOrg,
    document_id: UUID,
):
    """
    Export the risk report as a PDF CYA Package.
    Includes go/no-go recommendation, financial exposure, risk flags, and checklist.
    """
    from fastapi.responses import Response

    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.organization_id == organization.id,
    ).options(joinedload(Document.analysis)).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if not document.analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis found for this document",
        )

    # Build RiskReport from stored JSON
    risk_report_data = document.analysis.risk_report
    extraction_data = document.analysis.extraction_data

    # Create schema objects for export
    risk_report = RiskReport(**risk_report_data)
    extraction = SpecExtraction(**extraction_data) if extraction_data else None

    # Get project name
    project_name = document.project.name if document.project else None

    # Generate PDF
    pdf_content = export_service.generate_pdf(
        risk_report=risk_report,
        document_name=document.original_filename,
        project_name=project_name,
        extraction=extraction,
    )

    # Create filename
    safe_filename = document.original_filename.replace(".pdf", "").replace(" ", "_")
    export_filename = f"{safe_filename}_Risk_Report.pdf"

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"',
        }
    )


@router.get("/{document_id}/export-excel")
def export_risk_report_excel(
    *,
    db: DbSession,
    organization: CurrentOrg,
    document_id: UUID,
):
    """
    Export the risk report as an Excel spreadsheet.
    Includes risk log, summary, and checklist tabs.
    """
    from fastapi.responses import Response

    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.organization_id == organization.id,
    ).options(joinedload(Document.analysis)).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if not document.analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No analysis found for this document",
        )

    # Build RiskReport from stored JSON
    risk_report_data = document.analysis.risk_report
    extraction_data = document.analysis.extraction_data

    # Create schema objects for export
    risk_report = RiskReport(**risk_report_data)
    extraction = SpecExtraction(**extraction_data) if extraction_data else None

    # Get project name
    project_name = document.project.name if document.project else None

    # Generate Excel
    excel_content = export_service.generate_excel(
        risk_report=risk_report,
        document_name=document.original_filename,
        project_name=project_name,
        extraction=extraction,
    )

    # Create filename
    safe_filename = document.original_filename.replace(".pdf", "").replace(" ", "_")
    export_filename = f"{safe_filename}_Risk_Log.xlsx"

    return Response(
        content=excel_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"',
        }
    )
