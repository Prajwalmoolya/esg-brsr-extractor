# ESG Report Extractor

Extracts key ESG metrics (GHG emissions, energy, water, waste, workforce) from Indian BRSR and
sustainability report PDFs using an LLM with structured output, then validates every value
against the source page.

## How it works
1. **Read** the PDF page by page (pdfplumber)
2. **Filter** to pages with ESG keywords, cutting token cost
3. **Extract** metrics as structured JSON via the Claude API (tool use with a fixed schema)
4. **Validate**: each value must appear on its cited page; cross-checks such as female employees <= total
5. **Compare** companies side by side and export to CSV

## Results
_Add after testing: e.g. "XX% field-level accuracy across N reports and 10 metrics"_

## Run it
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key      # Windows: set ANTHROPIC_API_KEY=your_key
streamlit run app.py
```

## Limitations
- Scanned (image-only) PDFs return no text and need OCR
- Values split across complex tables can be missed; flagged rows need a manual check
