from extractor import extract_pages, find_relevant_pages

pages = extract_pages("reports/ultratech.pdf")
print("Total pages:", len(pages))
relevant = find_relevant_pages(pages)
print("Selected pages:", [p["page"] for p in relevant])