"""PDF text extraction service using pdfplumber with chunk metadata."""

import re
import uuid
import pdfplumber
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class TextChunk:
    """A chunk of text extracted from a PDF with metadata."""
    chunk_id: str
    page: int
    text: str
    start_index: int  # Character offset within the page
    end_index: int
    division: str | None = None
    section: str | None = None


class PDFIngestService:
    """
    Service for extracting text content from PDF files.
    Uses pdfplumber for reliable text extraction with chunk metadata.
    """

    # Regex patterns for detecting divisions and sections
    DIVISION_PATTERN = re.compile(
        r"(?:DIVISION|DIV\.?)\s*(\d{2})\s*[-–—]?\s*(.+?)(?:\n|$)",
        re.IGNORECASE
    )
    SECTION_PATTERN = re.compile(
        r"(?:SECTION\s*)?(\d{2}\s*\d{2}\s*\d{2}|\d{2}\s+\d{2}\s+\d{2})",
        re.IGNORECASE
    )

    def extract_text(self, file_path: str) -> tuple[str, int]:
        """
        Extract all text from a PDF file.
        Returns (full_text, page_count).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        text_parts = []
        page_count = 0

        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{page_text}")

        full_text = "\n\n".join(text_parts)
        return full_text, page_count

    def extract_text_by_page(self, file_path: str) -> list[dict]:
        """
        Extract text from each page with metadata.
        Returns list of {page_num, text, char_count}.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        pages = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                pages.append({
                    "page_num": page_num,
                    "text": page_text,
                    "char_count": len(page_text),
                })

        return pages

    def extract_chunks(self, file_path: str, chunk_size: int = 1500) -> list[TextChunk]:
        """
        Extract text from PDF as chunks with metadata.
        Each chunk includes page number, chunk_id, and position info.

        Args:
            file_path: Path to the PDF file
            chunk_size: Target size for each chunk in characters

        Returns:
            List of TextChunk objects with metadata
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        chunks = []
        current_division = None
        current_section = None

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                if not page_text.strip():
                    continue

                # Detect division changes on this page
                div_match = self.DIVISION_PATTERN.search(page_text)
                if div_match:
                    current_division = div_match.group(1)

                # Detect section numbers
                section_match = self.SECTION_PATTERN.search(page_text)
                if section_match:
                    current_section = section_match.group(1).replace(" ", " ")

                # Split page into chunks (by paragraphs or fixed size)
                page_chunks = self._split_into_chunks(page_text, chunk_size)

                for i, (chunk_text, start_idx, end_idx) in enumerate(page_chunks):
                    chunk_id = f"c_{page_num}_{i}"

                    # Check if this specific chunk has division/section markers
                    chunk_div = current_division
                    chunk_section = current_section

                    div_in_chunk = self.DIVISION_PATTERN.search(chunk_text)
                    if div_in_chunk:
                        chunk_div = div_in_chunk.group(1)

                    section_in_chunk = self.SECTION_PATTERN.search(chunk_text)
                    if section_in_chunk:
                        chunk_section = section_in_chunk.group(1).replace(" ", " ")

                    chunks.append(TextChunk(
                        chunk_id=chunk_id,
                        page=page_num,
                        text=chunk_text,
                        start_index=start_idx,
                        end_index=end_idx,
                        division=chunk_div,
                        section=chunk_section,
                    ))

        return chunks

    def _split_into_chunks(
        self, text: str, target_size: int
    ) -> list[tuple[str, int, int]]:
        """
        Split text into chunks, trying to break at paragraph boundaries.
        Returns list of (chunk_text, start_index, end_index).
        """
        if len(text) <= target_size:
            return [(text, 0, len(text))]

        chunks = []
        paragraphs = re.split(r'\n\s*\n', text)

        current_chunk = ""
        current_start = 0
        position = 0

        for para in paragraphs:
            para_with_break = para + "\n\n"

            if len(current_chunk) + len(para_with_break) > target_size and current_chunk:
                # Save current chunk
                chunks.append((
                    current_chunk.strip(),
                    current_start,
                    current_start + len(current_chunk)
                ))
                current_chunk = para_with_break
                current_start = position
            else:
                current_chunk += para_with_break

            position += len(para_with_break)

        # Add final chunk
        if current_chunk.strip():
            chunks.append((
                current_chunk.strip(),
                current_start,
                current_start + len(current_chunk)
            ))

        return chunks

    def chunks_to_dict_list(self, chunks: list[TextChunk]) -> list[dict]:
        """Convert TextChunk objects to list of dicts for JSON serialization."""
        return [asdict(chunk) for chunk in chunks]

    def build_chunked_text_for_llm(
        self,
        chunks: list[TextChunk],
        include_divisions: list[str] | None = None,
        max_chunks: int = 100
    ) -> str:
        """
        Build text with chunk markers for LLM analysis.

        Args:
            chunks: List of TextChunk objects
            include_divisions: If provided, only include chunks from these divisions
                             (e.g., ["00", "01", "22", "23", "26"])
            max_chunks: Maximum number of chunks to include

        Returns:
            Formatted text with [CHUNK_ID: ...][PAGE: ...] markers
        """
        filtered_chunks = chunks

        # Filter by division if specified
        if include_divisions:
            # Include chunks that match divisions OR have no division detected
            # (we want to include general content too)
            filtered_chunks = [
                c for c in chunks
                if c.division in include_divisions or c.division is None
            ]

        # Limit total chunks
        filtered_chunks = filtered_chunks[:max_chunks]

        parts = []
        for chunk in filtered_chunks:
            marker = f"[CHUNK_ID: {chunk.chunk_id}][PAGE: {chunk.page}]"
            if chunk.division:
                marker += f"[DIV: {chunk.division}]"
            if chunk.section:
                marker += f"[SECTION: {chunk.section}]"

            parts.append(f"{marker}\n{chunk.text}")

        return "\n\n---\n\n".join(parts)


# Singleton instance
pdf_ingest_service = PDFIngestService()
