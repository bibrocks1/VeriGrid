import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class ReasoningAgentError(Exception):
    """Raised when the reasoning agent cannot produce an assessment."""
    pass


def assess_hazard(
    question: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Use OpenAI to reason over grounded VeriGrid, MirEye and NOAA evidence.

    Returns:
        {
            "severity": "...",
            "explanation": "...",
            "recommended_action": "...",
            "evidence_summary": {...}
        }
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ReasoningAgentError(
            "OPENAI_API_KEY is not set in backend/.env"
        )

    client = OpenAI(api_key=api_key)

    system_prompt = """
You are the VeriGrid Hazard Reasoning Agent.

Your job is to assess real-world infrastructure and environmental
hazards using ONLY the evidence supplied to you.

The evidence comes from three separate sources:

1. VeriGrid
   Citizen-generated reports and verified hazard clusters.
   This tells you what people are observing on the ground.

2. MirEye
   Geospatial and infrastructure/terrain context around the location.
   This provides physical context that may help explain or assess
   the reported hazard.

3. NOAA
   Weather and forecast information.
   This provides environmental/weather context.

IMPORTANT RULES:

- Do not invent facts.
- Do not claim that a source says something it does not say.
- Clearly distinguish citizen observations from physical/geospatial
  evidence and weather evidence.
- If evidence is insufficient, explicitly say so.
- MirEye or NOAA evidence can SUPPORT or CONTRADICT a citizen report.
- Do not automatically assume that more reports means higher severity.
- Consider report count, confidence, recurrence, physical context,
  weather context and contradictions together.
- Severity must be exactly one of:
  "Low", "Medium", "High".

Return ONLY valid JSON with exactly these fields:

{
  "severity": "Low | Medium | High",
  "explanation": "Evidence-grounded explanation",
  "recommended_action": "Concrete recommended action",
  "evidence_summary": {
    "verigrid": "What VeriGrid evidence shows",
    "mireye": "What MirEye evidence shows",
    "noaa": "What NOAA evidence shows"
  }
}
"""

    user_prompt = f"""
User question:

{question}

Retrieved evidence:

{json.dumps(context, indent=2, default=str)}

Assess the hazard using the evidence above.
"""

    try:
        response = client.chat.completions.create(
            model=os.getenv(
                "OPENAI_REASONING_MODEL",
                "gpt-4o-mini",
            ),
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

    except Exception as exc:
        raise ReasoningAgentError(
            f"OpenAI reasoning request failed: {exc}"
        ) from exc

    content = response.choices[0].message.content

    if not content:
        raise ReasoningAgentError(
            "OpenAI returned an empty response."
        )

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ReasoningAgentError(
            "OpenAI returned invalid JSON."
        ) from exc

    required_fields = {
        "severity",
        "explanation",
        "recommended_action",
        "evidence_summary",
    }

    missing = required_fields - result.keys()

    if missing:
        raise ReasoningAgentError(
            f"Reasoning response is missing fields: {missing}"
        )

    if result["severity"] not in {"Low", "Medium", "High"}:
        raise ReasoningAgentError(
            f"Invalid severity: {result['severity']}"
        )

    return result   