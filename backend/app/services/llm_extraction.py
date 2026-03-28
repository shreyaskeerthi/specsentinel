"""LLM-based spec extraction using Claude API."""

import json
import anthropic

from app.core.config import settings
from app.schemas.analysis import (
    SpecExtraction, RiskFlag, RiskReport, RiskSeverity, RiskType, SpecLocation,
    Responsibility, CostImpact, CostImpactType, GoNoGo, GoNoGoRecommendation,
    FinancialExposure, RiskStatus
)
from app.services.pdf_ingest import TextChunk


class LLMExtractionService:
    """
    Service for extracting structured requirements using Claude API.
    Provides much better extraction quality than regex-based approach.
    """

    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def is_available(self) -> bool:
        """Check if LLM extraction is available."""
        return self.client is not None and settings.USE_LLM_EXTRACTION

    def extract(self, text: str, chunks: list[TextChunk] | None = None, max_text_length: int = 100000) -> SpecExtraction:
        """
        Extract structured requirements from spec text using Claude.
        """
        if not self.is_available():
            raise RuntimeError("LLM extraction not available - check ANTHROPIC_API_KEY")

        # Truncate text if too long
        if len(text) > max_text_length:
            text = text[:max_text_length] + "\n\n[... truncated ...]"

        prompt = f"""Analyze this construction specification document and extract key requirements.

Return a JSON object with these fields (use null if not found):
- insurance_requirements: Insurance coverage requirements (amounts, types, certificates needed)
- bonding_requirements: Performance bonds, payment bonds, bid bonds required
- warranty_requirements: Warranty periods and terms
- liquidated_damages: Liquidated damages/penalties (daily amounts, conditions)
- testing_requirements: Testing, TAB (testing/adjusting/balancing) requirements
- commissioning_requirements: Commissioning (Cx) requirements, functional testing
- submittals_summary: Submittal requirements summary
- div22_requirements: Division 22 (Plumbing) key requirements
- div23_requirements: Division 23 (HVAC) key requirements
- div26_requirements: Division 26 (Electrical) key requirements

Be concise but capture specific numbers, durations, and dollar amounts.

SPECIFICATION TEXT:
{text}

Return ONLY the JSON object, no other text."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        try:
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback to empty extraction
            data = {}

        return SpecExtraction(
            insurance_requirements=data.get("insurance_requirements"),
            bonding_requirements=data.get("bonding_requirements"),
            warranty_requirements=data.get("warranty_requirements"),
            liquidated_damages=data.get("liquidated_damages"),
            testing_requirements=data.get("testing_requirements"),
            commissioning_requirements=data.get("commissioning_requirements"),
            submittals_summary=data.get("submittals_summary"),
            div22_requirements=data.get("div22_requirements"),
            div23_requirements=data.get("div23_requirements"),
            div26_requirements=data.get("div26_requirements"),
        )

    def analyze_risks(
        self,
        text: str,
        extraction: SpecExtraction,
        chunks: list[TextChunk] | None = None,
        chunked_text: str | None = None
    ) -> RiskReport:
        """
        Generate a comprehensive bid risk report using Claude.

        Args:
            text: Raw text (fallback if no chunks)
            extraction: Previously extracted spec data
            chunks: List of TextChunk objects with metadata
            chunked_text: Pre-formatted text with chunk markers
        """
        if not self.is_available():
            raise RuntimeError("LLM extraction not available")

        # Use chunked text if available, otherwise fall back to raw text
        if chunked_text:
            analysis_text = chunked_text
        else:
            max_text_length = 80000
            if len(text) > max_text_length:
                text = text[:max_text_length] + "\n\n[... truncated ...]"
            analysis_text = text

        # Build prompt with chunk awareness
        chunk_instructions = ""
        if chunked_text:
            chunk_instructions = """
IMPORTANT - SOURCE ATTRIBUTION:
The text below contains markers like [CHUNK_ID: c_X_Y][PAGE: X] before each section.
For EVERY risk flag you identify, you MUST provide:
- "source_chunk_id": The chunk ID where you found this (e.g., "c_23_1")
- "source_page": The page number (integer)
- "source_quote": A SHORT direct quote (max 100 chars) from the spec that supports this risk

This is CRITICAL for allowing users to verify your findings in the original document.
"""

        prompt = f"""You are a senior MEP estimator reviewing this project manual for an HVAC/plumbing/electrical subcontractor preparing a bid.
{chunk_instructions}
PROJECT MANUAL EXCERPT:
---
{analysis_text}
---

Generate a BID RISK INTELLIGENCE REPORT. Return a JSON object:

{{
  "project_summary": {{
    "project_name": "string or null",
    "location": "string or null",
    "project_type": "school | hospital | commercial | industrial | residential | government | other",
    "scope_description": "string describing MEP-relevant scope",
    "schedule_constraints": "string or null",
    "occupied_building": true | false | null,
    "union_required": true | false | null
  }},
  "overall_risk_level": "low" | "medium" | "high" | "critical",
  "overall_summary": "1-2 sentence summary of risk profile",
  "go_no_go": {{
    "recommendation": "proceed" | "proceed_with_contingency" | "caution" | "do_not_bid",
    "contingency_percent": "number 0-25, suggested contingency percentage",
    "key_concerns": ["top concern 1", "top concern 2", "top concern 3"],
    "reasoning": "1-2 sentence explanation of recommendation"
  }},
  "flags": [
    {{
      "id": "R1",
      "category": "Warranty" | "Liquidated Damages" | "Bonds" | "Insurance" | "Testing/Commissioning" | "Submittals/Admin" | "Scope/Division Requirements" | "Schedule" | "Work Restrictions" | "Other",
      "type": "warranty" | "penalty" | "bonding" | "insurance" | "testing" | "commissioning" | "schedule" | "scope" | "other",
      "severity": "low" | "medium" | "high" | "critical",
      "title": "Short title (max 8 words)",
      "responsibility": "gc" | "mechanical" | "electrical" | "plumbing" | "controls" | "owner" | "shared" | "unknown",
      "source_chunk_id": "c_X_Y or null",
      "source_page": "integer or null",
      "source_quote": "Short direct quote (max 100 chars)",
      "spec_section": "Section number like '23 05 93' or null",
      "description": "1-2 sentence description",
      "impact": ["bullet 1", "bullet 2"],
      "recommended_action": ["action 1", "action 2"],
      "cost_impact": {{
        "type": "none" | "fixed" | "percentage" | "hourly" | "uncapped",
        "min_dollars": "number or null (e.g., 5000)",
        "max_dollars": "number or null (e.g., 25000)",
        "percentage_of_contract": "number or null (e.g., 2.5)",
        "description": "e.g., '$5,000-$25,000 added cost' or '+2-4% labor premium'"
      }}
    }}
  ],
  "estimator_checklist": {{
    "must_confirm_before_pricing": [
      {{"item": "description", "category": "Insurance" | "Bonds" | "Schedule" | "Scope" | "Other"}}
    ],
    "include_in_bid_cost": [
      {{"item": "description", "estimated_cost": "$X-$Y or +X% or null"}}
    ],
    "clarify_via_rfi": [
      {{"item": "description", "priority": "high" | "medium" | "low"}}
    ]
  }},
  "financial_exposure": {{
    "total_identified_min": "number - sum of all min cost impacts",
    "total_identified_max": "number - sum of all max cost impacts",
    "ld_daily_rate": "number or null - liquidated damages per day",
    "ld_cap": "number or null - LD cap if specified",
    "bond_percentage": "number or null - bond requirement %",
    "retention_percentage": "number or null - retention %"
  }}
}}

RULES:
1. COST IMPACTS MUST BE REAL NUMBERS: Estimate actual dollar ranges based on typical MEP project costs. For a $1M-$5M MEP contract:
   - Extended warranty (2yr): $8,000-$20,000
   - TAB/Commissioning: $15,000-$40,000
   - Restricted work hours: +8-15% labor premium
   - Performance bond: 1-3% of contract
   - LD exposure: Calculate based on daily rate × likely delay days

2. RESPONSIBILITY: Assign who bears this risk - gc, mechanical, electrical, plumbing, controls, owner, shared, or unknown.

3. GO/NO-GO: Be decisive. "proceed" = normal risk, "proceed_with_contingency" = add 3-10%, "caution" = add 10-15% or negotiate, "do_not_bid" = unacceptable risk.

4. Include flags for: Warranty, LD, Bonds, Insurance, Testing/Commissioning, Work Restrictions, Submittals. Create "Not specified in docs" flags for missing critical items.

5. Write like a senior estimator protecting their company, not a lawyer.

Return ONLY the JSON object."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        try:
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            data = json.loads(response_text)
        except json.JSONDecodeError:
            return RiskReport(
                overall_risk_level=RiskSeverity.LOW,
                overall_summary="Unable to analyze risks automatically.",
                flags=[],
                total_flags=0,
                high_severity_count=0,
            )

        # Parse flags
        flags = []
        for f in data.get("flags", []):
            try:
                # Map category to type
                type_map = {
                    "warranty": RiskType.WARRANTY,
                    "liquidated damages": RiskType.PENALTY,
                    "bonds": RiskType.BONDING,
                    "insurance": RiskType.INSURANCE,
                    "testing/commissioning": RiskType.TESTING,
                    "submittals/admin": RiskType.SCOPE,
                    "scope/division requirements": RiskType.SCOPE,
                    "schedule": RiskType.SCHEDULE,
                    "work restrictions": RiskType.SCHEDULE,
                }

                flag_type = f.get("type", "other")
                if flag_type not in [e.value for e in RiskType]:
                    flag_type = type_map.get(f.get("category", "").lower(), RiskType.OTHER)
                else:
                    flag_type = RiskType(flag_type)

                # Build SpecLocation from new source fields
                source_chunk_id = f.get("source_chunk_id")
                source_page = f.get("source_page")
                spec_section = f.get("spec_section")

                # Create structured SpecLocation if we have chunk/page data
                spec_location = None
                if source_chunk_id or source_page or spec_section:
                    spec_location = SpecLocation(
                        section=spec_section,
                        page=source_page if isinstance(source_page, int) else None,
                        chunk_id=source_chunk_id if source_chunk_id and source_chunk_id != "null" else None,
                    )

                # Parse responsibility
                resp_value = f.get("responsibility", "unknown")
                try:
                    responsibility = Responsibility(resp_value.lower() if resp_value else "unknown")
                except ValueError:
                    responsibility = Responsibility.UNKNOWN

                # Parse cost_impact
                cost_impact_data = f.get("cost_impact", {})
                cost_impact = None
                if cost_impact_data and isinstance(cost_impact_data, dict):
                    cost_type_str = cost_impact_data.get("type", "none")
                    try:
                        cost_type = CostImpactType(cost_type_str.lower() if cost_type_str else "none")
                    except ValueError:
                        cost_type = CostImpactType.NONE

                    cost_impact = CostImpact(
                        type=cost_type,
                        min_dollars=cost_impact_data.get("min_dollars"),
                        max_dollars=cost_impact_data.get("max_dollars"),
                        percentage_of_contract=cost_impact_data.get("percentage_of_contract"),
                        description=cost_impact_data.get("description"),
                    )

                flags.append(RiskFlag(
                    type=flag_type if isinstance(flag_type, RiskType) else RiskType(flag_type),
                    severity=RiskSeverity(f.get("severity", "medium")),
                    title=f.get("title", "Risk Identified"),
                    description=f.get("description", ""),
                    source_text=f.get("spec_quote"),  # Legacy field
                    source_quote=f.get("source_quote"),  # New field with short quote
                    spec_location=spec_location,
                    impact=f.get("impact", []),
                    recommended_action=f.get("recommended_action", []),
                    bid_cost_impact=f.get("bid_cost_impact"),
                    cost_impact=cost_impact,
                    responsibility=responsibility,
                    status=RiskStatus.OPEN,  # Default status
                    risk_id=f.get("id"),
                    category=f.get("category"),
                ))
            except (ValueError, KeyError):
                continue

        # Parse overall level
        try:
            overall_level = RiskSeverity(data.get("overall_risk_level", "medium"))
        except ValueError:
            overall_level = RiskSeverity.MEDIUM

        high_count = sum(1 for f in flags if f.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL])

        # Parse go_no_go
        go_no_go_data = data.get("go_no_go", {})
        go_no_go = None
        if go_no_go_data and isinstance(go_no_go_data, dict):
            rec_value = go_no_go_data.get("recommendation", "proceed")
            try:
                recommendation = GoNoGoRecommendation(rec_value.lower().replace(" ", "_") if rec_value else "proceed")
            except ValueError:
                recommendation = GoNoGoRecommendation.PROCEED

            go_no_go = GoNoGo(
                recommendation=recommendation,
                contingency_percent=go_no_go_data.get("contingency_percent", 0) or 0,
                key_concerns=go_no_go_data.get("key_concerns", []),
                reasoning=go_no_go_data.get("reasoning"),
            )

        # Parse financial_exposure
        fin_exp_data = data.get("financial_exposure", {})
        financial_exposure = None
        if fin_exp_data and isinstance(fin_exp_data, dict):
            financial_exposure = FinancialExposure(
                total_identified_min=fin_exp_data.get("total_identified_min", 0) or 0,
                total_identified_max=fin_exp_data.get("total_identified_max", 0) or 0,
                ld_daily_rate=fin_exp_data.get("ld_daily_rate"),
                ld_cap=fin_exp_data.get("ld_cap"),
                bond_percentage=fin_exp_data.get("bond_percentage"),
                retention_percentage=fin_exp_data.get("retention_percentage"),
            )

        return RiskReport(
            overall_risk_level=overall_level,
            overall_summary=data.get("overall_summary", "Risk analysis complete."),
            flags=flags,
            total_flags=len(flags),
            high_severity_count=high_count,
            project_summary=data.get("project_summary"),
            estimator_checklist=data.get("estimator_checklist"),
            go_no_go=go_no_go,
            financial_exposure=financial_exposure,
        )


# Singleton instance
llm_extraction_service = LLMExtractionService()
