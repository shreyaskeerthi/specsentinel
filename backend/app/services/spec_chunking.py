"""Spec document chunking and segmentation service."""

import re
from dataclasses import dataclass


@dataclass
class SpecSection:
    """A section extracted from the spec document."""
    division: str | None  # e.g., "00", "22", "23", "26"
    part: str | None  # e.g., "1", "2", "3"
    title: str
    content: str
    start_position: int
    end_position: int


class SpecChunkingService:
    """
    Service for segmenting construction spec documents.
    Identifies divisions (00, 01, 22, 23, 26) and parts (1-3).
    """

    # Regex patterns for division headers
    DIVISION_PATTERN = re.compile(
        r"(?:DIVISION|DIV\.?)\s*(\d{2})\s*[-–—]?\s*(.+?)(?:\n|$)",
        re.IGNORECASE | re.MULTILINE
    )

    # Regex patterns for part headers
    PART_PATTERN = re.compile(
        r"PART\s*(\d+)\s*[-–—]?\s*(.+?)(?:\n|$)",
        re.IGNORECASE | re.MULTILINE
    )

    # Regex for section headers (e.g., "1.01", "2.03")
    SECTION_PATTERN = re.compile(
        r"^(\d+\.\d{2})\s+(.+?)(?:\n|$)",
        re.MULTILINE
    )

    # Key divisions for MEP contractors
    MEP_DIVISIONS = {
        "00": "Procurement and Contracting",
        "01": "General Requirements",
        "22": "Plumbing",
        "23": "HVAC",
        "26": "Electrical",
    }

    def segment_document(self, text: str) -> list[SpecSection]:
        """
        Segment a spec document into sections by division and part.
        """
        sections = []

        # Find all division markers
        division_matches = list(self.DIVISION_PATTERN.finditer(text))

        if not division_matches:
            # No divisions found - treat entire document as one section
            sections.append(SpecSection(
                division=None,
                part=None,
                title="Full Document",
                content=text,
                start_position=0,
                end_position=len(text)
            ))
            return sections

        # Process each division
        for i, match in enumerate(division_matches):
            div_num = match.group(1)
            div_title = match.group(2).strip()

            # Determine end position (start of next division or end of doc)
            start_pos = match.start()
            if i + 1 < len(division_matches):
                end_pos = division_matches[i + 1].start()
            else:
                end_pos = len(text)

            div_content = text[start_pos:end_pos]

            # Find parts within this division
            part_matches = list(self.PART_PATTERN.finditer(div_content))

            if part_matches:
                # Create section for each part
                for j, part_match in enumerate(part_matches):
                    part_num = part_match.group(1)
                    part_title = part_match.group(2).strip()

                    part_start = part_match.start()
                    if j + 1 < len(part_matches):
                        part_end = part_matches[j + 1].start()
                    else:
                        part_end = len(div_content)

                    sections.append(SpecSection(
                        division=div_num,
                        part=part_num,
                        title=f"Division {div_num} - {div_title} - Part {part_num}: {part_title}",
                        content=div_content[part_start:part_end],
                        start_position=start_pos + part_start,
                        end_position=start_pos + part_end
                    ))
            else:
                # No parts - add entire division as one section
                sections.append(SpecSection(
                    division=div_num,
                    part=None,
                    title=f"Division {div_num} - {div_title}",
                    content=div_content,
                    start_position=start_pos,
                    end_position=end_pos
                ))

        return sections

    def extract_division_content(self, text: str, division: str) -> str | None:
        """Extract content for a specific division."""
        sections = self.segment_document(text)
        div_sections = [s for s in sections if s.division == division]

        if not div_sections:
            return None

        return "\n\n".join(s.content for s in div_sections)

    def extract_mep_divisions(self, text: str) -> dict[str, str | None]:
        """Extract content for all MEP-relevant divisions (22, 23, 26)."""
        return {
            "div22": self.extract_division_content(text, "22"),
            "div23": self.extract_division_content(text, "23"),
            "div26": self.extract_division_content(text, "26"),
            "div00": self.extract_division_content(text, "00"),
            "div01": self.extract_division_content(text, "01"),
        }


# Singleton instance
spec_chunking_service = SpecChunkingService()
