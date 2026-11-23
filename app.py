"""Streamlit front end: upload BRSR PDFs, extract every numeric data point, compare, download."""
import tempfile

import pandas as pd
import streamlit as st

from brsr_metrics import METRICS
from extractor import extract_metrics, extract_pages, find_relevant_pages, validate

st.set_page_config(page_title="ESG Report Extractor", layout="wide")
st.title("ESG Report Extractor")
st.caption(f"Extracts all {len(METRICS)} numeric BRSR data points (current year) from BRSR report PDFs.")

files = st.file_uploader("Upload BRSR PDF reports", type="pdf", accept_multiple_files=True)

if files and st.button("Extract metrics"):
    results = []
    for f in files:
        with st.status(f"Processing {f.name}...") as status:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(f.read())
                path = tmp.name

            pages = extract_pages(path)
            relevant = find_relevant_pages(pages)
            if not relevant:
                status.update(label=f"{f.name}: no readable text (scanned PDF?)", state="error")
                continue

            st.write(f"Sending {len(relevant)} of {len(pages)} pages to Claude in 7 requests (about 5-8 minutes)")
            result = extract_metrics(relevant)
            if result["failed_groups"]:
                st.write(f"Some parts failed: {', '.join(result['failed_groups'])}. Run this report again for those.")
            df = validate(result, pages)
            df.insert(0, "source_file", f.name)
            df.insert(1, "company", result.get("company_name") or f.name)
            df.insert(2, "financial_year", result.get("financial_year"))
            results.append(df)
            status.update(label=f"{f.name}: done", state="complete")

    if results:
        st.session_state["results"] = pd.concat(results, ignore_index=True)

if "results" in st.session_state:
    all_rows = st.session_state["results"]
    df = all_rows

    pillar = st.radio("Pillar", ["All", "Environment", "Social", "Governance"], horizontal=True)
    if pillar != "All":
        df = df[df["pillar"] == pillar]
        category = st.selectbox("Category", ["All"] + list(dict.fromkeys(df["category"])))
        if category != "All":
            df = df[df["category"] == category]
    if not st.checkbox("Show data points the report doesn't give", value=False):
        df = df[df["status"] != "not found"]

    flagged = all_rows[~all_rows["status"].isin(["OK", "not found", "calculated"])]
    st.caption(f"{(all_rows['status'] == 'OK').sum()} OK · {len(flagged)} need a manual check · "
               f"{(all_rows['status'] == 'not found').sum()} not reported · "
               f"{(all_rows['status'] == 'calculated').sum()} % values calculated")

    cols = ["company", "pillar", "category", "brsr_ref", "description", "value", "unit", "brsr_unit", "page", "status"]
    st.subheader("Extracted metrics")
    st.dataframe(df[cols], hide_index=True)

    if not flagged.empty:
        st.subheader("Needs a manual check")
        st.dataframe(flagged[cols], hide_index=True)

    st.subheader("Company comparison")
    st.dataframe(df.pivot_table(index=["pillar", "category", "brsr_ref", "metric"], columns="company",
                                values="value", aggfunc="first"))

    st.download_button("Download CSV", all_rows.to_csv(index=False), "esg_metrics.csv", "text/csv")
