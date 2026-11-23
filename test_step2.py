import json
from extractor import extract_pages, find_relevant_pages, extract_metrics, validate

pages = extract_pages("reports/ultratech.pdf")
relevant = find_relevant_pages(pages)
print(f"Sending {len(relevant)} pages to Claude... (takes 30-90 seconds)")

result = extract_metrics(relevant)
print(json.dumps(result, indent=2))

print("\n--- Validation ---")
df = validate(result, pages)
print(df[["metric", "value", "unit", "page", "status"]].to_string(index=False))