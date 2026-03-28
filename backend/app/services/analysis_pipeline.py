"""Main analysis pipeline orchestrating PDF processing and risk analysis."""

import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus
from app.models.analysis import AnalysisResult
from app.services.pdf_ingest import pdf_ingest_service
from app.services.spec_chunking import spec_chunking_service
from app.services.spec_extraction import spec_extraction_service
from app.services.risk_engine import risk_engine
from app.services.llm_extraction import llm_extraction_service
from app.schemas.analysis import SpecExtraction, RiskReport, DivisionData


class AnalysisPipeline:
    """
    Orchestrates the full analysis pipeline:
    1. PDF text extraction (with chunk metadata)
    2. Document segmentation
    3. Spec extraction (requirements identification)
    4. Risk analysis (with source attribution)
    """

    def process_document(self, db: Session, document: Document) -> AnalysisResult:
        """
        Process a document through the full analysis pipeline.
        Updates document status and creates AnalysisResult.
        """
        try:
            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            db.commit()

            # Step 1: Extract text from PDF with chunk metadata
            raw_text, page_count = pdf_ingest_service.extract_text(document.file_path)
            document.page_count = page_count

            # Step 1b: Extract chunks with metadata for source attribution
            chunks = pdf_ingest_service.extract_chunks(document.file_path)

            # Build chunked text with markers for LLM
            # Focus on MEP-relevant divisions: 00 (procurement), 01 (general), 22-26 (MEP)
            chunked_text = pdf_ingest_service.build_chunked_text_for_llm(
                chunks,
                include_divisions=["00", "01", "22", "23", "26"],
                max_chunks=100
            )

            # Step 2: Segment document into divisions
            division_data = spec_chunking_service.extract_mep_divisions(raw_text)

            # Step 3: Extract structured requirements
            # Use LLM extraction if available, fallback to regex
            if llm_extraction_service.is_available():
                extraction = llm_extraction_service.extract(raw_text, chunks)
                risk_report = llm_extraction_service.analyze_risks(
                    raw_text, extraction, chunks=chunks, chunked_text=chunked_text
                )
            else:
                extraction = spec_extraction_service.extract(raw_text, division_data)
                risk_report = risk_engine.analyze(extraction, raw_text)

            # Convert chunks to serializable format
            chunks_data = pdf_ingest_service.chunks_to_dict_list(chunks)

            # Create analysis result
            analysis_result = AnalysisResult(
                document_id=document.id,
                raw_text=raw_text[:50000] if raw_text else None,  # Limit stored text
                extraction_data=extraction.model_dump(),
                risk_report=risk_report.model_dump(),
                division_data={
                    "div22_plumbing": division_data.get("div22", "")[:5000] if division_data.get("div22") else None,
                    "div23_hvac": division_data.get("div23", "")[:5000] if division_data.get("div23") else None,
                    "div26_electrical": division_data.get("div26", "")[:5000] if division_data.get("div26") else None,
                    "div00_procurement": division_data.get("div00", "")[:5000] if division_data.get("div00") else None,
                    "div01_general": division_data.get("div01", "")[:5000] if division_data.get("div01") else None,
                },
                chunks_data=chunks_data,  # Store chunks for frontend navigation
            )

            db.add(analysis_result)
            document.status = DocumentStatus.COMPLETED
            db.commit()
            db.refresh(analysis_result)

            return analysis_result

        except Exception as e:
            # Mark document as failed
            document.status = DocumentStatus.FAILED
            db.commit()
            raise e

    def get_formatted_result(self, analysis: AnalysisResult) -> dict:
        """
        Format analysis result for API response.
        """
        extraction = SpecExtraction(**analysis.extraction_data)
        risk_report = RiskReport(**analysis.risk_report)
        division_data = DivisionData(**analysis.division_data) if analysis.division_data else None

        return {
            "id": analysis.id,
            "document_id": analysis.document_id,
            "extraction": extraction,
            "risk_report": risk_report,
            "division_data": division_data,
            "chunks": analysis.chunks_data,  # Include chunks for frontend navigation
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
        }


# Singleton instance
analysis_pipeline = AnalysisPipeline()
