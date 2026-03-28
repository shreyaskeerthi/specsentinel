"""LLM-based extraction using Claude API — spec analysis, meeting notes, emails."""

import json
import anthropic

from app.core.config import settings
from app.schemas.analysis import (
    SpecExtraction, RiskFlag, RiskReport, RiskSeverity, RiskType, SpecLocation,
    Responsibility, CostImpact, CostImpactType, GoNoGo, GoNoGoRecommendation,
    FinancialExposure, RiskStatus, ActionBoard, ActionTask, TaskPriority,
    TaskCategory, OwnerType, EmailSet, GeneratedEmail, MeetingAnalysis,
    MeetingDecision, MeetingRiskUpdate, MeetingTaskUpdate, MeetingAttendee,
)
from app.services.pdf_ingest import TextChunk


def _parse_json_response(text: str) -> dict:
    """Parse JSON from Claude response, handling markdown code blocks."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


class LLMExtractionService:
    """Claude-powered extraction for spec analysis, meeting notes, and emails."""

    def __init__(self):
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def is_available(self) -> bool:
        return self.client is not None and settings.USE_LLM_EXTRACTION

    def extract(self, text: str, chunks: list[TextChunk] | None = None, max_text_length: int = 100000) -> SpecExtraction:
        """Extract structured requirements from spec text."""
        if not self.is_available():
            raise RuntimeError("LLM extraction not available - check ANTHROPIC_API_KEY")

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
- closeout_requirements: Closeout documentation requirements
- schedule_requirements: Schedule milestones, duration, constraints
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

        try:
            data = _parse_json_response(message.content[0].text)
        except (json.JSONDecodeError, IndexError):
            data = {}

        return SpecExtraction(**{k: data.get(k) for k in SpecExtraction.model_fields})

    def analyze_risks(
        self,
        text: str,
        extraction: SpecExtraction,
        chunks: list[TextChunk] | None = None,
        chunked_text: str | None = None
    ) -> RiskReport:
        """Generate comprehensive bid risk report with action board."""
        if not self.is_available():
            raise RuntimeError("LLM extraction not available")

        analysis_text = chunked_text if chunked_text else text[:80000]

        chunk_instructions = ""
        if chunked_text:
            chunk_instructions = """
IMPORTANT - SOURCE ATTRIBUTION:
The text below contains markers like [CHUNK_ID: c_X_Y][PAGE: X] before each section.
For EVERY risk flag you identify, you MUST provide:
- "source_chunk_id": The chunk ID where you found this (e.g., "c_23_1")
- "source_page": The page number (integer)
- "source_quote": A SHORT direct quote (max 100 chars) from the spec that supports this risk
"""

        prompt = f"""You are a senior MEP estimator, construction risk analyst, and preconstruction advisor.

Analyze construction specs to identify financial risk, contractual traps, scope gaps, pricing implications, and execution burden.

{chunk_instructions}
PROJECT MANUAL:
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
    "contingency_percent": "number 0-25",
    "key_concerns": ["concern 1", "concern 2", "concern 3"],
    "reasoning": "1-2 sentence explanation"
  }},
  "flags": [
    {{
      "id": "R1",
      "category": "Warranty | Liquidated Damages | Bonds | Insurance | Testing/Commissioning | Submittals/Admin | Scope/Division Requirements | Schedule | Work Restrictions | Other",
      "type": "warranty | penalty | bonding | insurance | testing | commissioning | schedule | scope | other",
      "severity": "low | medium | high | critical",
      "title": "Short title (max 8 words)",
      "responsibility": "gc | mechanical | electrical | plumbing | controls | owner | shared | unknown",
      "source_chunk_id": "c_X_Y or null",
      "source_page": "integer or null",
      "source_quote": "Short direct quote (max 100 chars)",
      "spec_section": "Section number like '23 05 93' or null",
      "description": "1-2 sentence description of why this matters",
      "impact": ["bullet 1", "bullet 2"],
      "recommended_action": ["action 1", "action 2"],
      "cost_impact": {{
        "type": "none | fixed | percentage | hourly | uncapped",
        "min_dollars": "number or null",
        "max_dollars": "number or null",
        "percentage_of_contract": "number or null",
        "description": "e.g., '$5,000-$25,000 added cost'"
      }}
    }}
  ],
  "estimator_checklist": {{
    "must_confirm_before_pricing": [
      {{"item": "description", "category": "Insurance | Bonds | Schedule | Scope | Other"}}
    ],
    "include_in_bid_cost": [
      {{"item": "description", "estimated_cost": "$X-$Y or +X% or null"}}
    ],
    "clarify_via_rfi": [
      {{"item": "description", "priority": "high | medium | low"}}
    ]
  }},
  "financial_exposure": {{
    "total_identified_min": "number",
    "total_identified_max": "number",
    "ld_daily_rate": "number or null",
    "ld_cap": "number or null",
    "bond_percentage": "number or null",
    "retention_percentage": "number or null"
  }},
  "action_board": {{
    "to_clarify": [
      {{
        "id": "AC1",
        "title": "short title",
        "description": "what needs to be clarified and why",
        "priority": "high | medium | low",
        "owner_type": "Estimating | PM | Finance | Ops",
        "linked_risk_id": "R1 or null",
        "page_reference": "integer or null"
      }}
    ],
    "must_include": [
      {{
        "id": "BI1",
        "title": "short title",
        "description": "what must be included in the bid",
        "priority": "high | medium | low",
        "owner_type": "Estimating | PM | Finance | Ops",
        "linked_risk_id": "R1 or null",
        "page_reference": "integer or null"
      }}
    ],
    "internal": [
      {{
        "id": "IT1",
        "title": "short title",
        "description": "internal task or action item",
        "priority": "high | medium | low",
        "owner_type": "Estimating | PM | Finance | Ops",
        "linked_risk_id": "R1 or null",
        "page_reference": "integer or null"
      }}
    ]
  }}
}}

RULES:
1. COST IMPACTS MUST BE REAL NUMBERS for a $1M-$5M MEP contract:
   - Extended warranty (2yr): $8,000-$20,000
   - TAB/Commissioning: $15,000-$40,000
   - Restricted work hours: +8-15% labor premium
   - Performance bond: 1-3% of contract
   - LD exposure: Calculate based on daily rate x likely delay days
2. RESPONSIBILITY: Assign who bears this risk.
3. GO/NO-GO: Be decisive. "proceed" = normal risk, "proceed_with_contingency" = add 3-10%, "caution" = add 10-15%, "do_not_bid" = unacceptable risk.
4. ACTION BOARD: Generate at least 3 items per category. Link each to a risk ID when possible. Assign realistic owner types.
5. Write like a senior estimator protecting their company, not a lawyer.

Return ONLY the JSON object."""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            data = _parse_json_response(message.content[0].text)
        except (json.JSONDecodeError, IndexError):
            return RiskReport(
                overall_risk_level=RiskSeverity.MEDIUM,
                overall_summary="Unable to analyze risks automatically.",
                flags=[], total_flags=0, high_severity_count=0,
            )

        # Parse flags
        flags = self._parse_flags(data.get("flags", []))
        overall_level = self._parse_severity(data.get("overall_risk_level", "medium"))
        high_count = sum(1 for f in flags if f.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL])

        # Parse go_no_go
        go_no_go = self._parse_go_no_go(data.get("go_no_go", {}))
        financial_exposure = self._parse_financial_exposure(data.get("financial_exposure", {}))

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

    def parse_action_board(self, data: dict) -> ActionBoard:
        """Parse action board from LLM response data."""
        ab_data = data.get("action_board", {})
        if not ab_data or not isinstance(ab_data, dict):
            return ActionBoard()

        def parse_tasks(items: list, category: TaskCategory) -> list[ActionTask]:
            tasks = []
            for item in (items or []):
                if not isinstance(item, dict):
                    continue
                try:
                    priority = TaskPriority(item.get("priority", "medium").lower())
                except ValueError:
                    priority = TaskPriority.MEDIUM
                try:
                    owner = OwnerType(item.get("owner_type", "Estimating"))
                except ValueError:
                    owner = OwnerType.ESTIMATING
                tasks.append(ActionTask(
                    id=item.get("id", ""),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    priority=priority,
                    category=category,
                    owner_type=owner,
                    linked_risk_id=item.get("linked_risk_id"),
                    page_reference=item.get("page_reference"),
                ))
            return tasks

        return ActionBoard(
            to_clarify=parse_tasks(ab_data.get("to_clarify", []), TaskCategory.TO_CLARIFY),
            must_include=parse_tasks(ab_data.get("must_include", []), TaskCategory.MUST_INCLUDE),
            internal=parse_tasks(ab_data.get("internal", []), TaskCategory.INTERNAL),
        )

    def analyze_meeting_notes(self, notes: str, existing_analysis: dict | None = None) -> MeetingAnalysis:
        """Analyze meeting notes — returns NEW info to merge into existing analysis."""
        if not self.is_available():
            raise RuntimeError("LLM extraction not available")

        context = ""
        known_risk_ids = []
        if existing_analysis:
            rr = existing_analysis.get("risk_report", {})
            fin = rr.get("financial_exposure", {})
            flags = rr.get("flags", [])
            known_risk_ids = [f.get("risk_id") for f in flags if f.get("risk_id")]
            known_risks_summary = json.dumps([
                {"id": f.get("risk_id"), "title": f.get("title", "")}
                for f in flags[:15]
            ])
            ab = existing_analysis.get("action_board", {})
            all_tasks = [t for col in ab.values() for t in (col if isinstance(col, list) else [])]
            known_tasks_summary = json.dumps([
                {"id": t.get("id"), "title": t.get("title", ""), "status": t.get("status", "open"), "assignee": t.get("assignee")}
                for t in all_tasks[:20]
            ])
            context = f"""
EXISTING ANALYSIS (for context — only return NEW or CHANGED information from the meeting):
- Current exposure: ${fin.get('total_identified_min', 0):,} - ${fin.get('total_identified_max', 0):,}
- Current risk level: {rr.get('overall_risk_level', 'unknown')}
- Known risks (with IDs): {known_risks_summary}
- Recommendation: {(rr.get('go_no_go') or {}).get('recommendation', 'unknown')}
- Existing tasks (with IDs): {known_tasks_summary}
"""

        prompt = f"""You are a construction PM analyzing meeting minutes for an MEP subcontractor.
{context}
MEETING NOTES:
---
{notes[:15000]}
---

Extract ALL relevant information from this meeting. Return JSON:

{{
  "summary": "2-4 sentence narrative summary of what was discussed and decided",
  "attendees": [
    {{"name": "Full Name", "role": "their role/company or null"}}
  ],
  "key_decisions": [
    {{"decision": "what was decided", "impact": "financial/schedule/scope impact", "owner": "person or role"}}
  ],
  "new_risks": [
    {{
      "title": "short title",
      "severity": "low|medium|high|critical",
      "description": "why this is a risk — be specific",
      "cost_impact_min": 5000,
      "cost_impact_max": 20000,
      "cost_impact_description": "$5K-$20K for XYZ",
      "responsibility": "gc|mechanical|electrical|plumbing|owner|shared",
      "is_new": true,
      "related_risk_id": null
    }}
  ],
  "updated_tasks": [
    {{
      "title": "short actionable title",
      "priority": "high|medium|low",
      "category": "to_clarify|must_include|internal",
      "owner_type": "Estimating|PM|Finance|Ops",
      "description": "specific action needed",
      "due_date": "2026-04-10",
      "assignee": "person name or null",
      "linked_task_id": null,
      "new_status": null
    }}
  ],
  "schedule_events": [
    {{
      "title": "event name",
      "date": "2026-06-01",
      "type": "deadline|milestone|task|blackout|meeting",
      "description": "details"
    }}
  ],
  "financial_impact_summary": "How meeting changes total exposure. Be specific with dollar amounts.",
  "revised_exposure_min": 75000,
  "revised_exposure_max": 200000
}}

RULES:
1. summary: 2-4 sentence narrative of the meeting.
2. attendees: list everyone identified in the transcript.
3. new_risks with is_new=false: use related_risk_id to reference an EXISTING risk ID (e.g. "R3") when the meeting updates or acknowledges a known risk. Set is_new=true for genuinely new risks.
4. DATES: Use ISO format (YYYY-MM-DD). Extract ALL dates mentioned.
5. COSTS: Provide real dollar min/max for each new risk.
6. REVISED EXPOSURE: Calculate updated total including existing + new risks.
7. TASKS — two modes:
   a. NEW task: leave linked_task_id=null, new_status=null.
   b. UPDATE existing task: set linked_task_id to the matching task ID from "Existing tasks", set new_status to "open"|"in_progress"|"done" if the meeting changed it, set assignee if assigned in the meeting.

Return ONLY the JSON object."""

        from app.services.analysis_pipeline import _call_with_retry
        message = _call_with_retry(
            self.client,
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            data = _parse_json_response(message.content[0].text)
        except (json.JSONDecodeError, IndexError):
            return MeetingAnalysis()

        attendees = [
            MeetingAttendee(name=a.get("name", ""), role=a.get("role"))
            for a in data.get("attendees", [])
            if isinstance(a, dict) and a.get("name")
        ]

        decisions = [
            MeetingDecision(
                decision=d.get("decision", ""),
                impact=d.get("impact"),
                owner=d.get("owner"),
            )
            for d in data.get("key_decisions", [])
            if isinstance(d, dict)
        ]

        new_risks = []
        for r in data.get("new_risks", []):
            if isinstance(r, dict):
                new_risks.append(MeetingRiskUpdate(
                    title=r.get("title", ""),
                    severity=self._parse_severity(r.get("severity", "medium")),
                    description=r.get("description", ""),
                    cost_impact_min=r.get("cost_impact_min"),
                    cost_impact_max=r.get("cost_impact_max"),
                    cost_impact_description=r.get("cost_impact_description"),
                    responsibility=r.get("responsibility"),
                    is_new=r.get("is_new", True),
                    related_risk_id=r.get("related_risk_id"),
                ))

        tasks = []
        for t in data.get("updated_tasks", []):
            if isinstance(t, dict):
                try:
                    priority = TaskPriority(t.get("priority", "medium").lower())
                except ValueError:
                    priority = TaskPriority.MEDIUM
                try:
                    cat = TaskCategory(t.get("category", "internal").lower())
                except ValueError:
                    cat = TaskCategory.INTERNAL
                try:
                    owner = OwnerType(t.get("owner_type", "PM"))
                except ValueError:
                    owner = OwnerType.PM
                tasks.append(MeetingTaskUpdate(
                    title=t.get("title", ""),
                    priority=priority,
                    category=cat,
                    owner_type=owner,
                    description=t.get("description", ""),
                    due_date=t.get("due_date"),
                    assignee=t.get("assignee"),
                    linked_task_id=t.get("linked_task_id"),
                    new_status=t.get("new_status"),
                ))

        schedule_events = []
        for s in data.get("schedule_events", []):
            if isinstance(s, dict):
                from app.schemas.analysis import ScheduleEvent
                schedule_events.append(ScheduleEvent(
                    title=s.get("title", ""),
                    date=s.get("date", ""),
                    type=s.get("type", "task"),
                    description=s.get("description"),
                    linked_task_id=s.get("linked_task_id"),
                ))

        return MeetingAnalysis(
            summary=data.get("summary"),
            attendees=attendees,
            key_decisions=decisions,
            new_risks=new_risks,
            updated_tasks=tasks,
            schedule_events=schedule_events,
            financial_impact_summary=data.get("financial_impact_summary"),
            revised_exposure_min=data.get("revised_exposure_min"),
            revised_exposure_max=data.get("revised_exposure_max"),
        )

    def generate_emails(self, analysis: dict) -> EmailSet:
        """Generate RFI, internal alignment, and finance summary emails."""
        if not self.is_available():
            raise RuntimeError("LLM extraction not available")

        risk_report = analysis.get("risk_report", {})
        project_name = "the project"
        ps = risk_report.get("project_summary")
        if isinstance(ps, dict) and ps.get("project_name"):
            project_name = ps["project_name"]

        flags_summary = json.dumps([
            {"title": f.get("title", ""), "severity": f.get("severity", ""), "description": f.get("description", "")}
            for f in risk_report.get("flags", [])[:10]
        ])

        go_no_go = risk_report.get("go_no_go", {})
        fin = risk_report.get("financial_exposure", {})
        checklist = risk_report.get("estimator_checklist", {})
        rfi_items = checklist.get("clarify_via_rfi", []) if isinstance(checklist, dict) else []

        prompt = f"""You are a construction project manager and coordinator for an MEP subcontractor.

PROJECT: {project_name}
GO/NO-GO: {json.dumps(go_no_go)}
FINANCIAL EXPOSURE: {json.dumps(fin)}
TOP RISKS: {flags_summary}
RFI ITEMS: {json.dumps(rfi_items[:5])}

Generate exactly 3 emails as JSON:

{{
  "emails": [
    {{
      "type": "rfi",
      "subject": "RFI – [specific topic] – {project_name}",
      "recipients": "GC Project Manager / Owner Rep",
      "body": "Professional RFI email referencing spec sections. Ask clear questions. Include spec page references where possible."
    }},
    {{
      "type": "internal",
      "subject": "Bid Review: Key Risks & Required Actions – {project_name}",
      "recipients": "Estimating Team / Project Manager",
      "body": "Internal email summarizing key risks, required actions, and timeline. Include the go/no-go recommendation."
    }},
    {{
      "type": "finance",
      "subject": "Financial Exposure Summary – {project_name}",
      "recipients": "Finance / CFO",
      "body": "Finance-focused email with exposure range, contingency recommendation, top cost drivers, and bonding/insurance implications."
    }}
  ]
}}

REQUIREMENTS:
- Professional, concise, action-oriented tone
- Include specific dollar amounts and percentages from the analysis
- RFI email: reference spec sections, ask clear questions
- Internal email: list top 3 risks with costs, recommend next steps
- Finance email: total exposure range, contingency %, cost breakdown

Return ONLY the JSON object."""

        from app.services.analysis_pipeline import _call_with_retry
        message = _call_with_retry(
            self.client,
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            data = _parse_json_response(message.content[0].text)
        except (json.JSONDecodeError, IndexError):
            return EmailSet()

        emails = []
        for e in data.get("emails", []):
            if isinstance(e, dict):
                emails.append(GeneratedEmail(
                    type=e.get("type", ""),
                    subject=e.get("subject", ""),
                    recipients=e.get("recipients", ""),
                    body=e.get("body", ""),
                ))

        return EmailSet(emails=emails)

    # --- Helper methods ---

    def _parse_severity(self, value: str) -> RiskSeverity:
        try:
            return RiskSeverity(value.lower() if value else "medium")
        except ValueError:
            return RiskSeverity.MEDIUM

    def _parse_flags(self, raw_flags: list) -> list[RiskFlag]:
        flags = []
        for f in raw_flags:
            if not isinstance(f, dict):
                continue
            try:
                flag_type_str = f.get("type", "other")
                try:
                    flag_type = RiskType(flag_type_str.lower() if flag_type_str else "other")
                except ValueError:
                    flag_type = RiskType.OTHER

                spec_location = None
                source_chunk_id = f.get("source_chunk_id")
                source_page = f.get("source_page")
                spec_section = f.get("spec_section")
                if source_chunk_id or source_page or spec_section:
                    spec_location = SpecLocation(
                        section=spec_section,
                        page=source_page if isinstance(source_page, int) else None,
                        chunk_id=source_chunk_id if source_chunk_id and source_chunk_id != "null" else None,
                    )

                try:
                    responsibility = Responsibility(
                        (f.get("responsibility") or "unknown").lower()
                    )
                except ValueError:
                    responsibility = Responsibility.UNKNOWN

                cost_impact = None
                ci = f.get("cost_impact", {})
                if ci and isinstance(ci, dict):
                    try:
                        cost_type = CostImpactType((ci.get("type") or "none").lower())
                    except ValueError:
                        cost_type = CostImpactType.NONE
                    cost_impact = CostImpact(
                        type=cost_type,
                        min_dollars=ci.get("min_dollars"),
                        max_dollars=ci.get("max_dollars"),
                        percentage_of_contract=ci.get("percentage_of_contract"),
                        description=ci.get("description"),
                    )

                flags.append(RiskFlag(
                    type=flag_type,
                    severity=self._parse_severity(f.get("severity", "medium")),
                    title=f.get("title", "Risk Identified"),
                    description=f.get("description", ""),
                    source_text=f.get("spec_quote"),
                    source_quote=f.get("source_quote"),
                    spec_location=spec_location,
                    impact=f.get("impact", []),
                    recommended_action=f.get("recommended_action", []),
                    bid_cost_impact=f.get("bid_cost_impact"),
                    cost_impact=cost_impact,
                    responsibility=responsibility,
                    status=RiskStatus.OPEN,
                    risk_id=f.get("id"),
                    category=f.get("category"),
                ))
            except (ValueError, KeyError):
                continue
        return flags

    def _parse_go_no_go(self, data: dict) -> GoNoGo | None:
        if not data or not isinstance(data, dict):
            return None
        try:
            rec = GoNoGoRecommendation(
                (data.get("recommendation") or "proceed").lower().replace(" ", "_")
            )
        except ValueError:
            rec = GoNoGoRecommendation.PROCEED
        return GoNoGo(
            recommendation=rec,
            contingency_percent=data.get("contingency_percent", 0) or 0,
            key_concerns=data.get("key_concerns", []),
            reasoning=data.get("reasoning"),
        )

    def _parse_financial_exposure(self, data: dict) -> FinancialExposure | None:
        if not data or not isinstance(data, dict):
            return None
        return FinancialExposure(
            total_identified_min=data.get("total_identified_min", 0) or 0,
            total_identified_max=data.get("total_identified_max", 0) or 0,
            ld_daily_rate=data.get("ld_daily_rate"),
            ld_cap=data.get("ld_cap"),
            bond_percentage=data.get("bond_percentage"),
            retention_percentage=data.get("retention_percentage"),
        )

    def _build_risk_report(self, data: dict) -> RiskReport:
        """Build a RiskReport from raw dict (used by combined pipeline call)."""
        if not data:
            return RiskReport(
                overall_risk_level=RiskSeverity.MEDIUM,
                overall_summary="Unable to analyze.",
                flags=[], total_flags=0, high_severity_count=0,
            )
        flags = self._parse_flags(data.get("flags", []))
        overall_level = self._parse_severity(data.get("overall_risk_level", "medium"))
        high_count = sum(1 for f in flags if f.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL])
        return RiskReport(
            overall_risk_level=overall_level,
            overall_summary=data.get("overall_summary", "Risk analysis complete."),
            flags=flags,
            total_flags=len(flags),
            high_severity_count=high_count,
            project_summary=data.get("project_summary"),
            estimator_checklist=data.get("estimator_checklist"),
            go_no_go=self._parse_go_no_go(data.get("go_no_go", {})),
            financial_exposure=self._parse_financial_exposure(data.get("financial_exposure", {})),
        )


# Singleton
llm_extraction_service = LLMExtractionService()
