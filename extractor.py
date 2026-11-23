"""
ESG Report Extractor - core logic.
Reads a BRSR report PDF and extracts every numeric BRSR data point (see brsr_metrics.py)
as structured JSON, then validates the numbers.

The metrics are split into 7 groups (Section A, P1/P2/P7, P3 x2, P5, P6, P8/P9).
Each group is one request to Claude with only its own pages, and up to 3 run at once.
"""
import asyncio
import re

import pandas as pd
import pdfplumber
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from brsr_metrics import GROUPS, METRICS, NOT_MORE_THAN, SUM_CHECKS

# Uses your Claude Max login (no API key). "sonnet" = latest Sonnet model; "haiku" is lighter on usage limits.
MODEL = "sonnet"
PARALLEL_REQUESTS = 3     # lower to 1 or 2 if you hit usage limits


# ---------- Step 1: read the PDF ----------
def extract_pages(pdf_path):
    """Return a list of {'page': n, 'text': '...'} for every page."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            pages.append({"page": i, "text": page.extract_text() or ""})
    return pages


# ---------- Step 2: keep only the useful pages ----------
def _select_pages(pages, keywords, max_pages):
    scored = []
    for p in pages:
        text = p["text"].lower()
        score = sum(text.count(k) for k in keywords)
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return sorted([p for _, p in scored[:max_pages]], key=lambda p: p["page"])


def find_relevant_pages(pages):
    """All pages any group will use (pass the result, or all pages, to extract_metrics)."""
    chosen = {}
    for g in GROUPS.values():
        for p in _select_pages(pages, g["keywords"], g["max_pages"]):
            chosen[p["page"]] = p
    return [chosen[n] for n in sorted(chosen)]


# ---------- Step 3: ask Claude for structured output ----------
SYSTEM_PROMPT = """You extract data from Indian BRSR (Business Responsibility and Sustainability) reports.
Rules:
- Fill in EVERY metric in the list.
- Reports show the current and previous financial year side by side. Always take the CURRENT year.
- Copy numbers exactly as printed (remove commas). Never calculate, add up or estimate a value.
- Percentages: give the number only (45% -> 45).
- If the report writes "Nil", "0" or "-" for a metric, return 0.
- If the metric is not in the report at all, or is "NA" / "Not applicable", return value = null.
- If a metric asks for a combined figure that the report only gives split up, return null.
- Give the unit exactly as the report states it (e.g. GJ, kL, MT, %, Rs crore), and the page number
  (from the === PAGE n === markers) where you found it.
"""


def _schema(keys):
    item = {
        "type": "object",
        "properties": {
            "value": {"type": ["number", "null"]},
            "unit": {"type": ["string", "null"]},
            "page": {"type": ["integer", "null"]},
        },
        "required": ["value", "unit", "page"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "financial_year": {"type": "string", "description": "e.g. FY 2024-25"},
            "metrics": {
                "type": "object",
                "properties": {k: item for k in keys},
                "required": list(keys),          # Claude must answer every metric
                "additionalProperties": False,
            },
        },
        "required": ["company_name", "financial_year", "metrics"],
    }


async def _ask_claude(prompt_text, schema):
    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=[],               # no file/shell tools: Claude only reads the text we send
        setting_sources=[],     # ignore your personal Claude Code settings
        max_turns=8,
        output_format={"type": "json_schema", "schema": schema},
    )

    # Send the prompt as a stream (avoids Windows' command-line length limit for long reports)
    async def prompt_stream():
        yield {"type": "user", "message": {"role": "user", "content": prompt_text}}

    async for message in query(prompt=prompt_stream(), options=options):
        if isinstance(message, ResultMessage):
            if message.is_error or not message.structured_output:
                raise RuntimeError(f"Claude did not return structured output ({message.subtype})")
            return message.structured_output
    raise RuntimeError("No result received from Claude")


async def _extract_group(name, pages, limiter):
    keys = [k for k, m in METRICS.items() if m["group"] == name]
    cfg = GROUPS[name]
    selected = _select_pages(pages, cfg["keywords"], cfg["max_pages"])
    if not selected:
        return {"company_name": "", "financial_year": "", "metrics": {}}

    metric_list = "\n".join(f"- {k}: {METRICS[k]['desc']} [{METRICS[k]['ref']}] (unit: {METRICS[k]['unit']})" for k in keys)
    report_text = "\n\n".join(f"=== PAGE {p['page']} ===\n{p['text']}" for p in selected)
    prompt = f"Metrics to extract:\n{metric_list}\n\nReport pages:\n{report_text}"

    async with limiter:
        for attempt in range(2):           # one retry
            try:
                return await _ask_claude(prompt, _schema(keys))
            except Exception as err:
                last = err
        return last                        # returned (not raised) so the other groups still finish


async def _extract_all(pages):
    limiter = asyncio.Semaphore(PARALLEL_REQUESTS)
    names = list(GROUPS)
    results = await asyncio.gather(*[_extract_group(n, pages, limiter) for n in names])

    merged = {"company_name": "", "financial_year": "", "metrics": [], "failed_groups": []}
    found = {}
    for name, r in zip(names, results):
        if isinstance(r, Exception):
            merged["failed_groups"].append(name)
            continue
        merged["company_name"] = merged["company_name"] or r.get("company_name", "")
        merged["financial_year"] = merged["financial_year"] or r.get("financial_year", "")
        found.update(r.get("metrics", {}))
    for key, m in METRICS.items():
        entry = found.get(key) or {"value": None, "unit": None, "page": None}
        merged["metrics"].append({"metric": key, **entry, "failed": m["group"] in merged["failed_groups"]})
    return merged


def extract_metrics(pages):
    """Extract every metric. Pass all pages or the output of find_relevant_pages()."""
    return asyncio.run(_extract_all(pages))


# ---------- Step 4: validate (never trust the LLM blindly) ----------
def _numbers_on_page(text):
    cleaned = text.replace(",", "")
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", cleaned)]


def validate(result, pages):
    """Check each value appears on its cited page and passes basic sanity rules."""
    page_text = {p["page"]: p["text"] for p in pages}
    rows = []
    for m in result.get("metrics", []):
        info = METRICS.get(m["metric"], {})
        issues = []
        value, page = m.get("value"), m.get("page")
        if m.get("failed"):
            issues.append("extraction failed - run again")
        elif value is None:
            issues.append("not found")
        else:
            if value < 0:
                issues.append("negative value")
            if info.get("unit") == "%" and value > 100:
                issues.append("percentage above 100")
            # 0 usually appears as "Nil" or "-", so only look up non-zero numbers
            if value != 0:
                nums = _numbers_on_page(page_text.get(page, ""))
                tolerance = max(0.01, abs(value) * 0.001)
                if not any(abs(n - value) <= tolerance for n in nums):
                    issues.append("value not on cited page - check manually")
        rows.append({
            "pillar": info.get("pillar"), "category": info.get("category"), "brsr_ref": info.get("ref"),
            "metric": m["metric"], "description": info.get("desc"),
            "value": value, "unit": m.get("unit"), "brsr_unit": info.get("unit"), "page": page,
            "status": "; ".join(issues) or "OK",
        })

    df = pd.DataFrame(rows)
    vals = dict(zip(df["metric"], df["value"]))

    def flag(metric, msg):
        mask = df["metric"] == metric
        df.loc[mask, "status"] = df.loc[mask, "status"].map(lambda s: msg if s == "OK" else f"{s}; {msg}")

    def has(*keys):
        return all(pd.notna(vals.get(k)) for k in keys)

    for part, whole in NOT_MORE_THAN:
        if has(part, whole) and vals[part] > vals[whole]:
            flag(part, f"more than {whole} - check")

    for total, parts in SUM_CHECKS.items():
        found = [vals[p] for p in parts if pd.notna(vals.get(p))]
        if not has(total) or not found:
            continue
        parts_sum = sum(found)
        if abs(parts_sum - vals[total]) > max(1, abs(vals[total]) * 0.01):
            flag(total, f"parts add up to {parts_sum:,.2f}, not the total - check")

    # The BRSR "%" columns, calculated from the counts (e.g. % of permanent female employees with health insurance)
    calc = []
    for part, whole in NOT_MORE_THAN:
        if (whole.endswith("_total_count") or whole in ("board_total", "kmp_total")) and has(part, whole) and vals[whole] > 0:
            src = df[df["metric"] == part].iloc[0]
            calc.append({**src.to_dict(), "metric": f"{part}_pct", "description": f"{src['description']} (% of total)",
                         "value": round(vals[part] / vals[whole] * 100, 2), "unit": "%", "brsr_unit": "%",
                         "page": None, "status": "calculated"})
    if calc:
        df = pd.concat([df, pd.DataFrame(calc)], ignore_index=True)

    return df
