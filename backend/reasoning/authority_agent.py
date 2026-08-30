"""
Day 11 — Authority Agent.

Turns an already-assessed cluster (severity/explanation/recommended_action,
persisted by reasoning/assess_cluster.py on Day 10) into a structured,
evidence-backed complaint addressed to the responsible authority.

Deliberately reuses the same direct openai.OpenAI calling pattern as
reasoning/agent.py, not the unused llm/get_llm.py — that's what's
actually wired and tested elsewhere in this codebase, and introducing a
second LLM-calling mechanism here would just add more inconsistency to
clean up later, not less.
"""
import json
import os
import pathlib
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

AUTHORITY_MAPPING_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "authority_mapping.json"


class AuthorityAgentError(Exception):
    """Raised when the authority agent cannot produce a complaint."""
    pass


def _load_authority_mapping() -> dict[str, str]:
    with open(AUTHORITY_MAPPING_PATH, encoding="utf-8") as f:
        return json.load(f)


def generate_complaint(
    category: str,
    assessment: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Args:
        category: the cluster's ReportCategory value (e.g. "flooding").
        assessment: {"severity": ..., "explanation": ..., "recommended_action": ...}
                    — the already-persisted Day 10 assessment for this cluster.
        context: the same retrieve_context() evidence bundle used by the
                 reasoning agent (VeriGrid reports/clusters + MirEye + NOAA),
                 so the complaint can cite concrete evidence, not just
                 restate the assessment.

    Returns:
        {
            "title": "...",
            "description": "...",
            "severity": "...",
            "recommended_action": "...",
            "responsible_authority": "..."
        }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise AuthorityAgentError("OPENAI_API_KEY is not set in backend/.env")

    mapping = _load_authority_mapping()
    suggested_authority = mapping.get(category, mapping.get("other", "General Municipal Grievance Cell"))

    client = OpenAI(api_key=api_key)

    system_prompt = f"""
You are the VeriGrid Authority Complaint Agent.

Your job is to turn an already-assessed hazard cluster into a formal,
evidence-backed complaint addressed to the responsible local authority.

You are given:
1. A prior hazard assessment (severity, explanation, recommended action)
   produced by the VeriGrid Reasoning Agent.
2. The underlying evidence it was based on (citizen reports, verified
   clusters, MirEye geospatial context, NOAA weather context).
3. A suggested responsible authority for this report category, based on
   a fixed local mapping: "{suggested_authority}"

IMPORTANT RULES:
- Do not invent facts beyond what the assessment and evidence support.
- The description must be written as a formal complaint a citizen or
  civic body would submit to a government office — factual, concise,
  and evidence-referenced, not alarmist.
- Use the suggested responsible authority unless the evidence clearly
  indicates a different authority is more appropriate (e.g. a flooding
  report that is actually about a specific blocked storm drain might
  still route to the same department — do not overthink this; default
  to the suggested authority in ambiguous cases).
- Severity must be exactly one of: "Low", "Medium", "High" (carry over
  from the assessment provided; do not re-derive it).

Return ONLY valid JSON with exactly these fields:
{{
  "title": "Short complaint title",
  "description": "Formal, evidence-backed complaint description",
  "severity": "Low | Medium | High",
  "recommended_action": "Concrete recommended action for the authority",
  "responsible_authority": "Name of the responsible authority"
}}
"""

    user_prompt = f"""
Prior assessment:
{json.dumps(assessment, indent=2, default=str)}

Underlying evidence:
{json.dumps(context, indent=2, default=str)}

Generate the authority complaint.
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_REASONING_MODEL", "gpt-4o-mini"),
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:
        raise AuthorityAgentError(f"OpenAI request failed: {exc}") from exc

    content = response.choices[0].message.content
    if not content:
        raise AuthorityAgentError("OpenAI returned an empty response.")

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AuthorityAgentError("OpenAI returned invalid JSON.") from exc

    required_fields = {"title", "description", "severity", "recommended_action", "responsible_authority"}
    missing = required_fields - result.keys()
    if missing:
        raise AuthorityAgentError(f"Complaint response is missing fields: {missing}")

    if result["severity"] not in {"Low", "Medium", "High"}:
        raise AuthorityAgentError(f"Invalid severity: {result['severity']}")

    return result