"""Analysis pipeline — single LLM call, rate-limit safe."""

import json
import time
import uuid

import anthropic

from app.services.pdf_ingest import pdf_ingest_service
from app.services.spec_chunking import spec_chunking_service
from app.services.llm_extraction import llm_extraction_service, _parse_json_response
from app.schemas.analysis import ActionBoard


def _call_with_retry(client, max_retries=3, **kwargs):
    """Call Claude API with exponential backoff on rate limits."""
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait = (2 ** attempt) * 15  # 15s, 30s, 60s
            print(f"Rate limited, waiting {wait}s before retry {attempt + 2}...")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                wait = (2 ** attempt) * 15
                print(f"Rate limited, waiting {wait}s before retry {attempt + 2}...")
                time.sleep(wait)
            else:
                raise


class AnalysisPipeline:
    """Single-call analysis pipeline to stay within rate limits."""

    def process_document(self, file_path: str, filename: str) -> dict:
        """Process a PDF with ONE LLM call that returns everything."""

        if not llm_extraction_service.is_available():
            raise RuntimeError("ANTHROPIC_API_KEY not set.")

        # Step 1: Extract text + chunks
        raw_text, page_count = pdf_ingest_service.extract_text(file_path)
        chunks = pdf_ingest_service.extract_chunks(file_path)

        # Build chunked text — limit to 40 chunks (~25K chars) to stay under token limits
        chunked_text = pdf_ingest_service.build_chunked_text_for_llm(
            chunks,
            include_divisions=["00", "01", "22", "23", "26"],
            max_chunks=40,
        )

        # Truncate to ~25K chars max
        if len(chunked_text) > 25000:
            chunked_text = chunked_text[:25000] + "\n\n[... truncated for length ...]"

        # Step 2: Segment document by divisions (local, no LLM)
        division_data = spec_chunking_service.extract_mep_divisions(raw_text)

        # Step 3: ONE combined LLM call
        combined_result = self._combined_analysis(chunked_text)

        # Parse results
        extraction_data = combined_result.get("extraction", {})
        risk_data = combined_result.get("risk_report", {})
        action_board_data = combined_result.get("action_board", {})

        # Parse risk report through the service's parser
        risk_report = llm_extraction_service._build_risk_report(risk_data)
        action_board = llm_extraction_service.parse_action_board({"action_board": action_board_data})

        chunks_data = pdf_ingest_service.chunks_to_dict_list(chunks)

        return {
            "id": str(uuid.uuid4()),
            "filename": filename,
            "page_count": page_count,
            "extraction": extraction_data,
            "risk_report": risk_report.model_dump(),
            "division_data": {
                "div22_plumbing": (division_data.get("div22") or "")[:5000] or None,
                "div23_hvac": (division_data.get("div23") or "")[:5000] or None,
                "div26_electrical": (division_data.get("div26") or "")[:5000] or None,
                "div00_procurement": (division_data.get("div00") or "")[:5000] or None,
                "div01_general": (division_data.get("div01") or "")[:5000] or None,
            },
            "action_board": action_board.model_dump() if action_board else None,
            "chunks": chunks_data,
        }

    def _combined_analysis(self, text: str) -> dict:
        """Single LLM call that returns extraction + risk report + action board."""

        prompt = f"""You are a senior MEP estimator, construction risk analyst, and preconstruction advisor.

Analyze this construction spec and return a SINGLE JSON object with three top-level keys: "extraction", "risk_report", and "action_board".

The text contains [CHUNK_ID: c_X_Y][PAGE: X] markers. Reference these in source attribution.

SPEC TEXT:
---
{text}
---

Return this exact JSON structure:

{{
  "extraction": {{
    "insurance_requirements": "string or null",
    "bonding_requirements": "string or null",
    "warranty_requirements": "string or null",
    "liquidated_damages": "string or null",
    "testing_requirements": "string or null",
    "commissioning_requirements": "string or null",
    "submittals_summary": "string or null",
    "closeout_requirements": "string or null",
    "schedule_requirements": "string or null",
    "div22_requirements": "string or null",
    "div23_requirements": "string or null",
    "div26_requirements": "string or null"
  }},
  "risk_report": {{
    "project_summary": {{
      "project_name": "string or null",
      "location": "string or null",
      "project_type": "string",
      "scope_description": "string",
      "schedule_constraints": "string or null",
      "occupied_building": true|false|null,
      "union_required": true|false|null
    }},
    "overall_risk_level": "low|medium|high|critical",
    "overall_summary": "1-2 sentence summary",
    "go_no_go": {{
      "recommendation": "proceed|proceed_with_contingency|caution|do_not_bid",
      "contingency_percent": 0,
      "key_concerns": ["concern1", "concern2", "concern3"],
      "reasoning": "string"
    }},
    "flags": [
      {{
        "id": "R1",
        "category": "string",
        "type": "warranty|penalty|bonding|insurance|testing|commissioning|schedule|scope|other",
        "severity": "low|medium|high|critical",
        "title": "max 8 words",
        "responsibility": "gc|mechanical|electrical|plumbing|controls|owner|shared|unknown",
        "source_chunk_id": "c_X_Y or null",
        "source_page": 0,
        "source_quote": "max 100 chars",
        "description": "1-2 sentences",
        "impact": ["bullet1"],
        "recommended_action": ["action1"],
        "cost_impact": {{
          "type": "none|fixed|percentage|hourly|uncapped",
          "min_dollars": 0,
          "max_dollars": 0,
          "percentage_of_contract": null,
          "description": "string"
        }}
      }}
    ],
    "estimator_checklist": {{
      "must_confirm_before_pricing": [{{"item": "string", "category": "string"}}],
      "include_in_bid_cost": [{{"item": "string", "estimated_cost": "string"}}],
      "clarify_via_rfi": [{{"item": "string", "priority": "high|medium|low"}}]
    }},
    "financial_exposure": {{
      "total_identified_min": 0,
      "total_identified_max": 0,
      "ld_daily_rate": null,
      "ld_cap": null,
      "bond_percentage": null,
      "retention_percentage": null
    }}
  }},
  "action_board": {{
    "to_clarify": [
      {{"id": "AC1", "title": "string", "description": "string", "priority": "high|medium|low", "owner_type": "Estimating|PM|Finance|Ops", "linked_risk_id": "R1 or null", "page_reference": null}}
    ],
    "must_include": [
      {{"id": "BI1", "title": "string", "description": "string", "priority": "high|medium|low", "owner_type": "Estimating|PM|Finance|Ops", "linked_risk_id": "R1 or null", "page_reference": null}}
    ],
    "internal": [
      {{"id": "IT1", "title": "string", "description": "string", "priority": "high|medium|low", "owner_type": "Estimating|PM|Finance|Ops", "linked_risk_id": "R1 or null", "page_reference": null}}
    ]
  }}
}}

RULES:
1. COST IMPACTS: Use real dollar estimates for a $1M-$5M MEP contract.
2. GO/NO-GO: Be decisive. Include contingency %.
3. ACTION BOARD: 3-5 items per category, linked to risk IDs.
4. SOURCE ATTRIBUTION: Every flag needs source_chunk_id, source_page, source_quote.
5. Write like a senior estimator, not a lawyer.

Return ONLY the JSON object."""

        message = _call_with_retry(
            llm_extraction_service.client,
            model="claude-sonnet-4-20250514",
            max_tokens=5000,
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return _parse_json_response(message.content[0].text)
        except (json.JSONDecodeError, IndexError):
            return {}


analysis_pipeline = AnalysisPipeline()
