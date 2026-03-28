"""Spec extraction service - extracts key requirements using regex patterns."""

import re
from dataclasses import dataclass

from app.schemas.analysis import SpecExtraction


@dataclass
class ExtractionMatch:
    """A matched extraction with context."""
    text: str
    context: str
    confidence: float


class SpecExtractionService:
    """
    Service for extracting structured requirements from spec documents.
    Uses regex patterns for MVP; TODO: integrate LLM for better extraction.
    """

    # Insurance patterns
    INSURANCE_PATTERNS = [
        re.compile(r"(?:insurance|liability).{0,200}(?:\$[\d,]+|\d+[\s,]*(?:million|thousand))", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:general liability|professional liability|workers.{0,5}comp).{0,150}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:certificate of insurance|COI|insurance requirements).{0,200}", re.IGNORECASE | re.DOTALL),
    ]

    # Bonding patterns
    BONDING_PATTERNS = [
        re.compile(r"(?:performance bond|payment bond|bid bond).{0,200}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:surety|bonding).{0,100}(?:required|shall|must).{0,100}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:bond).{0,50}(?:\d+%|percent).{0,100}", re.IGNORECASE | re.DOTALL),
    ]

    # Warranty patterns
    WARRANTY_PATTERNS = [
        re.compile(r"(?:warranty|warrantee|guarantee).{0,150}(?:\d+\s*(?:year|month|day)).{0,50}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:\d+\s*(?:year|month)).{0,50}(?:warranty|warrantee|guarantee)", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:manufacturer.{0,20}warrant|extended warrant).{0,150}", re.IGNORECASE | re.DOTALL),
    ]

    # Liquidated damages patterns
    LD_PATTERNS = [
        re.compile(r"(?:liquidated damages?).{0,200}(?:\$[\d,]+|\d+).{0,50}(?:per day|daily|per calendar day)", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:\$[\d,]+|\d+).{0,50}(?:per day|daily).{0,50}(?:liquidated|damages?|penalty)", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:delay damages?|penalty|penalt).{0,100}(?:\$[\d,]+).{0,50}", re.IGNORECASE | re.DOTALL),
    ]

    # Testing patterns
    TESTING_PATTERNS = [
        re.compile(r"(?:TAB|testing.{0,10}adjusting.{0,10}balancing).{0,200}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:test|testing).{0,50}(?:require|shall|must).{0,150}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:pressure test|hydrostatic test|leak test).{0,150}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:third.party|independent).{0,50}(?:test|inspection).{0,100}", re.IGNORECASE | re.DOTALL),
    ]

    # Commissioning patterns
    CX_PATTERNS = [
        re.compile(r"(?:commission|Cx|CxA).{0,200}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:functional.performance.test|FPT).{0,150}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:pre.functional|startup|start.up).{0,100}(?:checklist|test|require).{0,100}", re.IGNORECASE | re.DOTALL),
    ]

    # Submittal patterns
    SUBMITTAL_PATTERNS = [
        re.compile(r"(?:submittal|shop drawing|product data).{0,200}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:submit).{0,50}(?:for approval|for review).{0,100}", re.IGNORECASE | re.DOTALL),
        re.compile(r"(?:submittal schedule|submittal register).{0,150}", re.IGNORECASE | re.DOTALL),
    ]

    def _find_best_match(self, text: str, patterns: list[re.Pattern]) -> str | None:
        """Find the best (longest) match from a list of patterns."""
        all_matches = []
        for pattern in patterns:
            matches = pattern.findall(text)
            all_matches.extend(matches)

        if not all_matches:
            return None

        # Return the longest match, cleaned up
        best = max(all_matches, key=len)
        # Clean up whitespace
        best = re.sub(r"\s+", " ", best).strip()
        # Truncate if too long
        if len(best) > 500:
            best = best[:500] + "..."
        return best

    def _find_all_matches(self, text: str, patterns: list[re.Pattern], max_results: int = 3) -> list[str]:
        """Find all unique matches from patterns."""
        all_matches = set()
        for pattern in patterns:
            matches = pattern.findall(text)
            for m in matches:
                cleaned = re.sub(r"\s+", " ", m).strip()
                if len(cleaned) > 20:  # Filter out very short matches
                    all_matches.add(cleaned[:300])

        # Return top matches by length
        sorted_matches = sorted(all_matches, key=len, reverse=True)
        return sorted_matches[:max_results]

    def extract(self, text: str, division_data: dict[str, str | None] | None = None) -> SpecExtraction:
        """
        Extract structured requirements from spec text.
        Optionally use division-specific content for better extraction.
        """
        # Use full text for general requirements
        insurance = self._find_best_match(text, self.INSURANCE_PATTERNS)
        bonding = self._find_best_match(text, self.BONDING_PATTERNS)
        warranty = self._find_best_match(text, self.WARRANTY_PATTERNS)
        liquidated_damages = self._find_best_match(text, self.LD_PATTERNS)
        testing = self._find_best_match(text, self.TESTING_PATTERNS)
        commissioning = self._find_best_match(text, self.CX_PATTERNS)
        submittals = self._find_best_match(text, self.SUBMITTAL_PATTERNS)

        # Division-specific extractions
        div22 = None
        div23 = None
        div26 = None

        if division_data:
            if division_data.get("div22"):
                div22_matches = self._find_all_matches(division_data["div22"], self.TESTING_PATTERNS + self.CX_PATTERNS)
                div22 = " | ".join(div22_matches) if div22_matches else self._summarize_division(division_data["div22"])

            if division_data.get("div23"):
                div23_matches = self._find_all_matches(division_data["div23"], self.TESTING_PATTERNS + self.CX_PATTERNS)
                div23 = " | ".join(div23_matches) if div23_matches else self._summarize_division(division_data["div23"])

            if division_data.get("div26"):
                div26_matches = self._find_all_matches(division_data["div26"], self.TESTING_PATTERNS + self.CX_PATTERNS)
                div26 = " | ".join(div26_matches) if div26_matches else self._summarize_division(division_data["div26"])

        return SpecExtraction(
            insurance_requirements=insurance,
            bonding_requirements=bonding,
            warranty_requirements=warranty,
            liquidated_damages=liquidated_damages,
            testing_requirements=testing,
            commissioning_requirements=commissioning,
            submittals_summary=submittals,
            div22_requirements=div22,
            div23_requirements=div23,
            div26_requirements=div26,
        )

    def _summarize_division(self, text: str, max_length: int = 500) -> str:
        """Create a brief summary of division content."""
        # Simple summarization: take first N characters
        cleaned = re.sub(r"\s+", " ", text).strip()
        if len(cleaned) <= max_length:
            return cleaned
        return cleaned[:max_length] + "..."


# Singleton instance
spec_extraction_service = SpecExtractionService()
