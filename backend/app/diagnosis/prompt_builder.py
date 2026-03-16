"""
PromptBuilder — constructs the LLM prompt from raw machine data.

The prompt is designed to elicit a structured JSON response from Gemini.
It provides:
  - Machine metadata
  - All current sensor readings with threshold context
  - Recent error codes
  - Recent log lines (if include_logs=True)
  - Any rule-engine soft matches (confidence < threshold) as hints
  - Explicit JSON output schema instruction

The output schema instruction is critical — response_parser.py depends on it.
"""
import json
from typing import List, Optional

from app.diagnosis.rules_engine import RuleMatch


OUTPUT_SCHEMA_INSTRUCTION = """
Respond ONLY with a valid JSON object matching this exact schema (no markdown, no explanation):
{
  "diagnosis": "<one concise sentence describing the root cause>",
  "recommended_action": "<specific step-by-step action for the field technician>",
  "severity": "<one of: low | medium | high | critical>",
  "confidence_score": <float between 0.0 and 1.0>,
  "supporting_evidence": [
    {"description": "<observation>", "source": "<sensor|log|error_code|pattern>"}
  ]
}
"""


class PromptBuilder:
    def build(
        self,
        machine_id: str,
        raw_data: dict,
        include_logs: bool = True,
        rule_hints: Optional[List[RuleMatch]] = None,
    ) -> str:
        info = raw_data.get("info", {})
        sensors = raw_data.get("sensors", [])
        errors = raw_data.get("errors", [])
        logs = raw_data.get("logs", [])

        lines: List[str] = []

        lines.append("You are an expert industrial maintenance AI assistant.")
        lines.append("Analyze the following machine telemetry and provide a diagnosis.\n")

        # Machine metadata
        lines.append("## Machine Information")
        lines.append(f"- ID: {machine_id}")
        lines.append(f"- Name: {info.get('name', machine_id)}")
        lines.append(f"- Type: {info.get('type', 'unknown')}")
        lines.append(f"- Location: {info.get('location', 'unknown')}\n")

        # Sensor readings
        lines.append("## Current Sensor Readings")
        if sensors:
            for s in sensors:
                warn = s.get("threshold_warning")
                crit = s.get("threshold_critical")
                thresholds = ""
                if warn is not None or crit is not None:
                    thresholds = f" [warn>{warn}, crit>{crit}]"
                status_flag = f" *** STATUS: {s.get('status','normal').upper()} ***" if s.get("status", "normal") != "normal" else ""
                lines.append(f"- {s.get('name')}: {s.get('value')} {s.get('unit','')}{thresholds}{status_flag}")
        else:
            lines.append("- NO SENSOR DATA AVAILABLE")
        lines.append("")

        # Recent error codes
        lines.append("## Recent Error Codes")
        if errors:
            for e in errors:
                lines.append(f"- {e}")
        else:
            lines.append("- None")
        lines.append("")

        # Log lines
        if include_logs and logs:
            lines.append("## Recent Log Lines (last 20)")
            for log_line in logs[-20:]:
                lines.append(f"  {log_line.rstrip()}")
            lines.append("")

        # Rule hints
        if rule_hints:
            lines.append("## Preliminary Rule-Based Observations (for context)")
            for hint in rule_hints:
                lines.append(f"- [{hint.severity.value.upper()}] {hint.diagnosis} (confidence: {hint.confidence:.0%})")
            lines.append("")

        lines.append("## Task")
        lines.append(
            "Based on all the above data, identify the most likely root cause of any issues. "
            "If the machine appears healthy, state that clearly with low severity."
        )
        lines.append("")
        lines.append(OUTPUT_SCHEMA_INSTRUCTION)

        return "\n".join(lines)
