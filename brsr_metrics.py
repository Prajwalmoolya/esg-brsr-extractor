"""
Complete list of numeric BRSR data points (current financial year), following SEBI's
BRSR format (May 2021) as updated with the BRSR Core KPIs (July 2023).

Each metric has:
  pillar    Environment / Social / Governance
  group     which Claude request extracts it (one request per group, see GROUPS)
  category  a readable heading for the app
  ref       where it sits in the BRSR (section, principle, indicator, question)
  desc      what to extract
  unit      the standard BRSR unit

Left out on purpose:
  - previous-year columns (only the current year is extracted)
  - "%" columns that are just (number / total) of a count we already extract - they are
    calculated in code instead of asked from Claude
  - free-length lists (business activities, products by NIC code, subsidiaries, CSR projects,
    R&R projects, LCA, top-10 associations): their number of rows differs per company
  - text, Yes/No and narrative answers
"""

METRICS = {}
SUM_CHECKS = {}       # total -> [parts]  (total must equal the sum of the parts)
NOT_MORE_THAN = []    # (part, whole)     (part must not exceed the whole)


def add(key, pillar, group, category, ref, desc, unit):
    METRICS[key] = dict(pillar=pillar, group=group, category=category, ref=ref, desc=desc, unit=unit)


SEXES = [("total", "Total"), ("male", "Male"), ("female", "Female")]

# =====================================================================================
# SECTION A - GENERAL DISCLOSURES
# =====================================================================================
G, P = "section_a", "Governance"
add("paid_up_capital", P, G, "Company", "Sec A · Q11", "Paid-up capital", "INR")
for where, w in [("national", "National"), ("international", "International")]:
    add(f"plants_{where}", P, G, "Company", "Sec A · Q16", f"Number of plants: {w}", "count")
    add(f"offices_{where}", P, G, "Company", "Sec A · Q16", f"Number of offices: {w}", "count")
add("markets_states_count", P, G, "Company", "Sec A · Q17(a)", "Markets served: National (No. of States)", "count")
add("markets_countries_count", P, G, "Company", "Sec A · Q17(a)", "Markets served: International (No. of Countries)", "count")
add("export_turnover_pct", P, G, "Company", "Sec A · Q17(b)", "Contribution of exports as a % of total turnover", "%")

# Q18 employees and workers, Q18(b) differently abled
for prefix, label, cat, q in [("", "", "Workforce", "Q18(a)"),
                              ("differently_abled_", "Differently abled ", "Differently abled", "Q18(b)")]:
    for grp, glabel in [("permanent_employees", "Permanent employees (D)"),
                        ("other_employees", "Other than permanent employees (E)"),
                        ("total_employees", "Total employees (D+E)"),
                        ("permanent_workers", "Permanent workers (F)"),
                        ("other_workers", "Other than permanent workers (G)"),
                        ("total_workers", "Total workers (F+G)")]:
        for sex, slabel in SEXES:
            add(f"{prefix}{grp}_{sex}", "Social", G, cat, f"Sec A · {q}",
                f"{label}{glabel}: {slabel}", "count")
        SUM_CHECKS[f"{prefix}{grp}_total"] = [f"{prefix}{grp}_male", f"{prefix}{grp}_female"]
    for kind in ["employees", "workers"]:
        for sex, _ in SEXES:
            SUM_CHECKS[f"{prefix}total_{kind}_{sex}"] = [f"{prefix}permanent_{kind}_{sex}", f"{prefix}other_{kind}_{sex}"]
NOT_MORE_THAN += [("differently_abled_total_employees_total", "total_employees_total"),
                  ("differently_abled_total_workers_total", "total_workers_total")]

# Q19 women
for role, rlabel in [("board", "Board of Directors"), ("kmp", "Key Management Personnel")]:
    add(f"{role}_total", P, G, "Board & leadership", "Sec A · Q19", f"{rlabel}: total (A)", "count")
    add(f"{role}_women", P, G, "Board & leadership", "Sec A · Q19", f"{rlabel}: no. of females (B)", "count")
    NOT_MORE_THAN.append((f"{role}_women", f"{role}_total"))

# Q20 turnover rate
for grp, glabel in [("employees", "Permanent employees"), ("workers", "Permanent workers")]:
    for sex, slabel in SEXES:
        add(f"turnover_rate_{grp}_{sex}_pct", "Social", G, "Workforce", "Sec A · Q20",
            f"Turnover rate, {glabel}: {slabel} (current FY)", "%")

# Q22 CSR
add("csr_turnover", P, G, "Company", "Sec A · Q22(ii)", "Turnover (in Rs.) given under CSR details", "INR")
add("csr_net_worth", P, G, "Company", "Sec A · Q22(iii)", "Net worth (in Rs.) given under CSR details", "INR")

# Q23 complaints by stakeholder group
for sh, slabel in [("communities", "Communities"), ("investors", "Investors (other than shareholders)"),
                   ("shareholders", "Shareholders"), ("employees_workers", "Employees and workers"),
                   ("customers", "Customers"), ("value_chain", "Value Chain Partners"), ("other", "Other")]:
    add(f"grievances_{sh}_filed", P, G, "Stakeholder grievances", "Sec A · Q23",
        f"{slabel}: number of complaints filed during the year", "count")
    add(f"grievances_{sh}_pending", P, G, "Stakeholder grievances", "Sec A · Q23",
        f"{slabel}: number of complaints pending resolution at close of the year", "count")
    NOT_MORE_THAN.append((f"grievances_{sh}_pending", f"grievances_{sh}_filed"))

# =====================================================================================
# PRINCIPLES 1, 2, 7 - ethics, products, policy advocacy
# =====================================================================================
G = "p1_p2_p7"
P = "Governance"
for grp, glabel in [("board", "Board of Directors"), ("kmp", "Key Managerial Personnel"),
                    ("employees", "Employees other than BoD and KMPs"), ("workers", "Workers")]:
    add(f"ethics_programmes_{grp}", P, G, "Ethics training", "P1 · EI 1",
        f"{glabel}: total number of training and awareness programmes held", "count")
    add(f"ethics_training_{grp}_pct", P, G, "Ethics training", "P1 · EI 1",
        f"{glabel}: % of persons covered by the awareness programmes", "%")
add("fines_penalties_amount", P, G, "Fines & penalties", "P1 · EI 2", "Monetary: penalty / fine amount (total)", "INR")
add("settlement_amount", P, G, "Fines & penalties", "P1 · EI 2", "Monetary: settlement amount (total)", "INR")
add("compounding_fee_amount", P, G, "Fines & penalties", "P1 · EI 2", "Monetary: compounding fee amount (total)", "INR")
for grp, glabel in [("directors", "Directors"), ("kmp", "KMPs"), ("employees", "Employees"), ("workers", "Workers")]:
    add(f"corruption_action_{grp}", P, G, "Anti-corruption", "P1 · EI 5",
        f"{glabel} against whom disciplinary action was taken for bribery / corruption", "count")
add("conflict_of_interest_directors", P, G, "Anti-corruption", "P1 · EI 6",
    "Complaints received on conflict of interest of the Directors", "count")
add("conflict_of_interest_kmp", P, G, "Anti-corruption", "P1 · EI 6",
    "Complaints received on conflict of interest of the KMPs", "count")
add("accounts_payable_days", P, G, "Openness of business", "P1 · EI 8",
    "Number of days of accounts payables ((accounts payable x 365) / cost of goods or services procured)", "days")
for key, desc, unit in [
    ("purchases_trading_houses_pct", "Purchases from trading houses as % of total purchases", "%"),
    ("trading_houses_count", "Number of trading houses where purchases are made from", "count"),
    ("purchases_top10_trading_houses_pct", "Purchases from top 10 trading houses as % of total purchases from trading houses", "%"),
    ("sales_dealers_pct", "Sales to dealers / distributors as % of total sales", "%"),
    ("dealers_count", "Number of dealers / distributors to whom sales are made", "count"),
    ("sales_top10_dealers_pct", "Sales to top 10 dealers / distributors as % of total sales to dealers / distributors", "%"),
    ("rpt_purchases_pct", "Share of RPTs in purchases (% of total purchases)", "%"),
    ("rpt_sales_pct", "Share of RPTs in sales (% of total sales)", "%"),
    ("rpt_loans_advances_pct", "Share of RPTs in loans and advances (% of total loans and advances)", "%"),
    ("rpt_investments_pct", "Share of RPTs in investments (% of total investments)", "%"),
]:
    add(key, P, G, "Openness of business", "P1 · EI 9", desc, unit)
add("value_chain_awareness_programmes", P, G, "Ethics training", "P1 · LI 1",
    "Total number of awareness programmes held for value chain partners", "count")
add("value_chain_awareness_pct", P, G, "Ethics training", "P1 · LI 1",
    "% of value chain partners covered (by value of business done) under awareness programmes", "%")

P = "Environment"
add("rnd_sustainable_tech_pct", P, G, "Products", "P2 · EI 1",
    "R&D investments in specific technologies to improve environmental and social impacts (% of total R&D)", "%")
add("capex_sustainable_tech_pct", P, G, "Products", "P2 · EI 1",
    "Capex investments in specific technologies to improve environmental and social impacts (% of total capex)", "%")
add("sustainable_inputs_pct", P, G, "Products", "P2 · EI 2(b)", "Percentage of inputs sourced sustainably", "%")
add("recycled_input_material_pct", P, G, "Products", "P2 · LI 3",
    "Recycled or re-used input material to total material (%)", "%")
for cat, clabel in [("plastics", "Plastics (including packaging)"), ("e_waste", "E-waste"),
                    ("hazardous", "Hazardous waste"), ("other", "Other waste")]:
    for how, hlabel in [("reused", "Re-used"), ("recycled", "Recycled"), ("disposed", "Safely disposed")]:
        add(f"reclaimed_{cat}_{how}", P, G, "Reclaimed products", "P2 · LI 4",
            f"Products and packaging reclaimed at end of life, {clabel}: {hlabel}", "t")

add("trade_association_affiliations", "Governance", G, "Policy advocacy", "P7 · EI 1(a)",
    "Number of affiliations with trade and industry chambers / associations", "count")

# =====================================================================================
# PRINCIPLE 3 - employee well-being (split in two requests)
# =====================================================================================
G, P = "p3_benefits", "Social"
BENEFITS = [("total_count", "Total (A)"), ("health_insurance", "No. covered by health insurance"),
            ("accident_insurance", "No. covered by accident insurance"), ("maternity", "No. covered by maternity benefits"),
            ("paternity", "No. covered by paternity benefits"), ("day_care", "No. covered by day care facilities")]
for grp, glabel, q in [("permanent_employees", "Permanent employees", "EI 1(a)"),
                       ("other_employees", "Other than permanent employees", "EI 1(a)"),
                       ("permanent_workers", "Permanent workers", "EI 1(b)"),
                       ("other_workers", "Other than permanent workers", "EI 1(b)")]:
    cat = "Benefits – employees" if "employees" in grp else "Benefits – workers"
    for sex, slabel in SEXES:
        for col, clabel in BENEFITS:
            add(f"benefit_{grp}_{sex}_{col}", P, G, cat, f"P3 · {q}", f"{glabel}, {slabel}: {clabel}", "count")
            if col != "total_count":
                NOT_MORE_THAN.append((f"benefit_{grp}_{sex}_{col}", f"benefit_{grp}_{sex}_total_count"))
    for col, _ in BENEFITS:
        SUM_CHECKS[f"benefit_{grp}_total_{col}"] = [f"benefit_{grp}_male_{col}", f"benefit_{grp}_female_{col}"]
add("wellbeing_spend_pct_revenue", P, G, "Benefits – employees", "P3 · EI 1(c)",
    "Cost incurred on well-being measures as a % of total revenue of the company", "%")
for b, blabel in [("pf", "PF"), ("gratuity", "Gratuity"), ("esi", "ESI"), ("other", "Others")]:
    add(f"retirement_{b}_employees_pct", P, G, "Retirement benefits", "P3 · EI 2",
        f"{blabel}: employees covered as a % of total employees", "%")
    add(f"retirement_{b}_workers_pct", P, G, "Retirement benefits", "P3 · EI 2",
        f"{blabel}: workers covered as a % of total workers", "%")
for grp, glabel in [("employees", "Permanent employees"), ("workers", "Permanent workers")]:
    for rate, rlabel in [("return_to_work", "Return to work rate"), ("retention", "Retention rate")]:
        for sex, slabel in SEXES:
            add(f"parental_{grp}_{rate}_{sex}_pct", P, G, "Parental leave", "P3 · EI 5",
                f"{glabel} who took parental leave, {rlabel}: {slabel}", "%")
for grp, glabel in [("permanent_employees", "Total permanent employees"), ("permanent_workers", "Total permanent workers")]:
    for sex, slabel in SEXES:
        add(f"union_{grp}_{sex}_total_count", P, G, "Union membership", "P3 · EI 7",
            f"{glabel}, {slabel}: total in respective category", "count")
        add(f"union_{grp}_{sex}_members", P, G, "Union membership", "P3 · EI 7",
            f"{glabel}, {slabel}: no. who are part of associations or unions", "count")
        NOT_MORE_THAN.append((f"union_{grp}_{sex}_members", f"union_{grp}_{sex}_total_count"))

G = "p3_training_safety"
for grp, glabel in [("employees", "Employees"), ("workers", "Workers")]:
    for sex, slabel in SEXES:
        add(f"training_{grp}_{sex}_total_count", P, G, "Training", "P3 · EI 8", f"{glabel}, {slabel}: total (A)", "count")
        add(f"training_{grp}_{sex}_health_safety", P, G, "Training", "P3 · EI 8",
            f"{glabel}, {slabel}: no. given training on health and safety measures", "count")
        add(f"training_{grp}_{sex}_skill_upgradation", P, G, "Training", "P3 · EI 8",
            f"{glabel}, {slabel}: no. given skill upgradation training", "count")
        add(f"review_{grp}_{sex}_total_count", P, G, "Career reviews", "P3 · EI 9", f"{glabel}, {slabel}: total", "count")
        add(f"review_{grp}_{sex}_reviewed", P, G, "Career reviews", "P3 · EI 9",
            f"{glabel}, {slabel}: no. receiving regular performance and career development reviews", "count")
        for c in ["health_safety", "skill_upgradation"]:
            NOT_MORE_THAN.append((f"training_{grp}_{sex}_{c}", f"training_{grp}_{sex}_total_count"))
        NOT_MORE_THAN.append((f"review_{grp}_{sex}_reviewed", f"review_{grp}_{sex}_total_count"))
    for c in ["total_count", "health_safety", "skill_upgradation"]:
        SUM_CHECKS[f"training_{grp}_total_{c}"] = [f"training_{grp}_male_{c}", f"training_{grp}_female_{c}"]
for grp, glabel in [("employees", "Employees"), ("workers", "Workers")]:
    for key, desc, unit in [
        ("ltifr", "Lost Time Injury Frequency Rate (LTIFR) per one million person-hours worked", "rate"),
        ("recordable_injuries", "Total recordable work-related injuries", "count"),
        ("fatalities", "No. of fatalities", "count"),
        ("high_consequence_injuries", "High consequence work-related injury or ill-health (excluding fatalities)", "count"),
        ("permanent_disabilities", "No. of permanent disabilities", "count"),
    ]:
        add(f"{key}_{grp}", P, G, "Health & safety", "P3 · EI 11", f"{desc}: {glabel}", unit)
for topic, tlabel in [("working_conditions", "Working conditions"), ("health_safety", "Health & safety")]:
    add(f"complaints_{topic}_filed", P, G, "Workplace complaints", "P3 · EI 13", f"{tlabel}: complaints filed during the year", "count")
    add(f"complaints_{topic}_pending", P, G, "Workplace complaints", "P3 · EI 13", f"{tlabel}: pending resolution at end of year", "count")
    NOT_MORE_THAN.append((f"complaints_{topic}_pending", f"complaints_{topic}_filed"))
    add(f"assessed_{topic}_pct", P, G, "Assessments", "P3 · EI 14", f"{tlabel}: % of plants and offices assessed", "%")
    add(f"value_chain_assessed_{topic}_pct", P, G, "Assessments", "P3 · LI 5",
        f"{tlabel}: % of value chain partners (by value of business) assessed", "%")
for grp, glabel in [("employees", "Employees"), ("workers", "Workers")]:
    add(f"high_consequence_affected_{grp}", P, G, "Health & safety", "P3 · LI 3",
        f"{glabel}: total no. affected by high consequence work-related injury / ill-health / fatalities", "count")
    add(f"high_consequence_rehabilitated_{grp}", P, G, "Health & safety", "P3 · LI 3",
        f"{glabel}: no. rehabilitated and placed in suitable employment (or family member placed)", "count")
    NOT_MORE_THAN.append((f"high_consequence_rehabilitated_{grp}", f"high_consequence_affected_{grp}"))

# =====================================================================================
# PRINCIPLE 5 - human rights
# =====================================================================================
G, P = "p5", "Social"
for grp, glabel in [("employees", "Employees"), ("workers", "Workers")]:
    for typ, tlabel in [("permanent", "Permanent"), ("other", "Other than permanent"), ("total", "Total")]:
        add(f"hr_training_{grp}_{typ}_total_count", P, G, "Human rights training", "P5 · EI 1",
            f"{glabel}, {tlabel}: total (A)", "count")
        add(f"hr_training_{grp}_{typ}_trained", P, G, "Human rights training", "P5 · EI 1",
            f"{glabel}, {tlabel}: no. given training on human rights issues and policies", "count")
        NOT_MORE_THAN.append((f"hr_training_{grp}_{typ}_trained", f"hr_training_{grp}_{typ}_total_count"))
    for c in ["total_count", "trained"]:
        SUM_CHECKS[f"hr_training_{grp}_total_{c}"] = [f"hr_training_{grp}_permanent_{c}", f"hr_training_{grp}_other_{c}"]
    for typ, tlabel in [("permanent", "Permanent"), ("other", "Other than permanent")]:
        for sex, slabel in SEXES:
            base = f"min_wage_{grp}_{typ}_{sex}"
            add(f"{base}_total_count", P, G, "Minimum wages", "P5 · EI 2", f"{glabel}, {tlabel}, {slabel}: total (A)", "count")
            add(f"{base}_equal", P, G, "Minimum wages", "P5 · EI 2",
                f"{glabel}, {tlabel}, {slabel}: no. paid equal to minimum wage", "count")
            add(f"{base}_above", P, G, "Minimum wages", "P5 · EI 2",
                f"{glabel}, {tlabel}, {slabel}: no. paid more than minimum wage", "count")
        for c in ["total_count", "equal", "above"]:
            SUM_CHECKS[f"min_wage_{grp}_{typ}_total_{c}"] = [f"min_wage_{grp}_{typ}_male_{c}", f"min_wage_{grp}_{typ}_female_{c}"]
for role, rlabel in [("board", "Board of Directors (BoD)"), ("kmp", "Key Managerial Personnel"),
                     ("employees", "Employees other than BoD and KMP"), ("workers", "Workers")]:
    for sex, slabel in [("male", "Male"), ("female", "Female")]:
        add(f"median_{role}_{sex}_count", P, G, "Remuneration", "P5 · EI 3(a)", f"{rlabel}, {slabel}: number", "count")
        add(f"median_{role}_{sex}_pay", P, G, "Remuneration", "P5 · EI 3(a)",
            f"{rlabel}, {slabel}: median remuneration / salary / wages", "INR")
add("female_wages_pct", P, G, "Remuneration", "P5 · EI 3(b)", "Gross wages paid to females as % of total wages", "%")
for topic, tlabel in [("sexual_harassment", "Sexual harassment"), ("discrimination", "Discrimination at workplace"),
                      ("child_labour", "Child labour"), ("forced_labour", "Forced labour / involuntary labour"),
                      ("wages", "Wages"), ("other_hr", "Other human rights related issues")]:
    add(f"complaints_{topic}_filed", P, G, "Human rights complaints", "P5 · EI 6", f"{tlabel}: filed during the year", "count")
    add(f"complaints_{topic}_pending", P, G, "Human rights complaints", "P5 · EI 6", f"{tlabel}: pending resolution at end of year", "count")
    NOT_MORE_THAN.append((f"complaints_{topic}_pending", f"complaints_{topic}_filed"))
add("posh_complaints_total", P, G, "Human rights complaints", "P5 · EI 7",
    "Total complaints reported under the POSH Act", "count")
add("posh_complaints_pct_female", P, G, "Human rights complaints", "P5 · EI 7",
    "Complaints on POSH as a % of female employees / workers", "%")
add("posh_complaints_upheld", P, G, "Human rights complaints", "P5 · EI 7", "Complaints on POSH upheld", "count")
NOT_MORE_THAN.append(("posh_complaints_upheld", "posh_complaints_total"))
for topic, tlabel in [("child_labour", "Child labour"), ("forced_labour", "Forced / involuntary labour"),
                      ("sexual_harassment", "Sexual harassment"), ("discrimination", "Discrimination at workplace"),
                      ("wages", "Wages")]:
    add(f"assessed_{topic}_pct", P, G, "Assessments", "P5 · EI 9", f"{tlabel}: % of plants and offices assessed", "%")
    add(f"value_chain_assessed_{topic}_pct", P, G, "Assessments", "P5 · LI 4",
        f"{tlabel}: % of value chain partners (by value of business) assessed", "%")

# =====================================================================================
# PRINCIPLE 6 - environment
# =====================================================================================
G, P = "p6", "Environment"
for key, desc in [
    ("renewable_electricity", "From renewable sources: total electricity consumption (A)"),
    ("renewable_fuel", "From renewable sources: total fuel consumption (B)"),
    ("renewable_other", "From renewable sources: energy consumption through other sources (C)"),
    ("renewable_energy_consumption", "Total energy consumed from renewable sources (A+B+C)"),
    ("non_renewable_electricity", "From non-renewable sources: total electricity consumption (D)"),
    ("non_renewable_fuel", "From non-renewable sources: total fuel consumption (E)"),
    ("non_renewable_other", "From non-renewable sources: energy consumption through other sources (F)"),
    ("non_renewable_energy_consumption", "Total energy consumed from non-renewable sources (D+E+F)"),
    ("total_energy_consumption", "Total energy consumed (A+B+C+D+E+F)"),
]:
    add(key, P, G, "Energy", "P6 · EI 1", desc, "GJ")
for key, desc, unit in [
    ("energy_intensity_turnover", "Energy intensity per rupee of turnover", "GJ/INR"),
    ("energy_intensity_ppp", "Energy intensity per rupee of turnover adjusted for PPP", "GJ/INR (PPP)"),
    ("energy_intensity_physical", "Energy intensity in terms of physical output", "GJ/unit"),
    ("energy_intensity_optional", "Energy intensity (optional) - the relevant metric chosen by the entity", "as stated"),
]:
    add(key, P, G, "Energy", "P6 · EI 1", desc, unit)

for src, slabel in [("surface", "(i) Surface water"), ("groundwater", "(ii) Groundwater"), ("third_party", "(iii) Third party water"),
                    ("seawater", "(iv) Seawater / desalinated water"), ("others", "(v) Others")]:
    add(f"water_{src}", P, G, "Water", "P6 · EI 3", f"Water withdrawal by source: {slabel}", "kL")
add("total_water_withdrawal", P, G, "Water", "P6 · EI 3", "Total volume of water withdrawal (i+ii+iii+iv+v)", "kL")
add("total_water_consumption", P, G, "Water", "P6 · EI 3", "Total volume of water consumption", "kL")
for key, desc, unit in [
    ("water_intensity_turnover", "Water intensity per rupee of turnover (total water consumption / revenue)", "kL/INR"),
    ("water_intensity_ppp", "Water intensity per rupee of turnover adjusted for PPP", "kL/INR (PPP)"),
    ("water_intensity_physical", "Water intensity in terms of physical output", "kL/unit"),
    ("water_intensity_optional", "Water intensity (optional) - the relevant metric chosen by the entity", "as stated"),
]:
    add(key, P, G, "Water", "P6 · EI 3", desc, unit)
parts = []
for dest, dlabel in [("surface", "(i) To surface water"), ("groundwater", "(ii) To groundwater"), ("seawater", "(iii) To seawater"),
                     ("third_party", "(iv) Sent to third-parties"), ("others", "(v) Others")]:
    for t, tlabel in [("no_treatment", "No treatment"), ("with_treatment", "With treatment")]:
        add(f"discharge_{dest}_{t}", P, G, "Water discharge", "P6 · EI 4", f"Water discharge {dlabel}: {tlabel}", "kL")
        parts.append(f"discharge_{dest}_{t}")
add("total_water_discharged", P, G, "Water discharge", "P6 · EI 4", "Total water discharged", "kL")
SUM_CHECKS["total_water_discharged"] = parts

for gas, glabel in [("nox", "NOx"), ("sox", "SOx"), ("pm", "Particulate matter (PM)"),
                    ("pop", "Persistent organic pollutants (POP)"), ("voc", "Volatile organic compounds (VOC)"),
                    ("hap", "Hazardous air pollutants (HAP)")]:
    add(f"air_{gas}", P, G, "Air emissions", "P6 · EI 6", f"{glabel} emissions", "as stated")

add("scope1_emissions", P, G, "GHG emissions", "P6 · EI 7", "Total Scope 1 emissions", "tCO2e")
add("scope2_emissions", P, G, "GHG emissions", "P6 · EI 7", "Total Scope 2 emissions", "tCO2e")
for key, desc, unit in [
    ("ghg_intensity_turnover", "Total Scope 1 and Scope 2 emissions per rupee of turnover", "tCO2e/INR"),
    ("ghg_intensity_ppp", "Total Scope 1 and Scope 2 emissions per rupee of turnover adjusted for PPP", "tCO2e/INR (PPP)"),
    ("ghg_intensity_physical", "Total Scope 1 and Scope 2 emission intensity in terms of physical output", "tCO2e/unit"),
    ("ghg_intensity_optional", "Total Scope 1 and Scope 2 emission intensity (optional)", "as stated"),
]:
    add(key, P, G, "GHG emissions", "P6 · EI 7", desc, unit)

waste_parts = []
for w, wlabel in [("plastic", "Plastic waste (A)"), ("e_waste", "E-waste (B)"), ("bio_medical", "Bio-medical waste (C)"),
                  ("construction", "Construction and demolition waste (D)"), ("battery", "Battery waste (E)"),
                  ("radioactive", "Radioactive waste (F)"), ("other_hazardous", "Other hazardous waste (G)"),
                  ("other_non_hazardous", "Other non-hazardous waste generated (H)")]:
    add(f"waste_{w}", P, G, "Waste", "P6 · EI 9", f"Waste generated: {wlabel}", "t")
    waste_parts.append(f"waste_{w}")
add("total_waste_generated", P, G, "Waste", "P6 · EI 9", "Total waste generated (A+B+C+D+E+F+G+H)", "t")
SUM_CHECKS["total_waste_generated"] = waste_parts
for key, desc, unit in [
    ("waste_intensity_turnover", "Waste intensity per rupee of turnover", "t/INR"),
    ("waste_intensity_ppp", "Waste intensity per rupee of turnover adjusted for PPP", "t/INR (PPP)"),
    ("waste_intensity_physical", "Waste intensity in terms of physical output", "t/unit"),
    ("waste_intensity_optional", "Waste intensity (optional)", "as stated"),
]:
    add(key, P, G, "Waste", "P6 · EI 9", desc, unit)
for key, desc in [("waste_recycled", "Waste recovered: (i) Recycled"), ("waste_reused", "Waste recovered: (ii) Re-used"),
                  ("waste_other_recovery", "Waste recovered: (iii) Other recovery operations"),
                  ("total_waste_recovered", "Total waste recovered"),
                  ("waste_incineration", "Waste disposed: (i) Incineration"), ("waste_landfill", "Waste disposed: (ii) Landfilling"),
                  ("waste_other_disposal", "Waste disposed: (iii) Other disposal operations"),
                  ("total_waste_disposed", "Total waste disposed")]:
    add(key, P, G, "Waste", "P6 · EI 9", desc, "t")
SUM_CHECKS["total_waste_recovered"] = ["waste_recycled", "waste_reused", "waste_other_recovery"]
SUM_CHECKS["total_waste_disposed"] = ["waste_incineration", "waste_landfill", "waste_other_disposal"]

# Leadership: water-stress areas (totals across all such facilities)
for src, slabel in [("surface", "Surface water"), ("groundwater", "Groundwater"), ("third_party", "Third party water"),
                    ("seawater", "Seawater / desalinated water"), ("others", "Others")]:
    add(f"stress_water_{src}", P, G, "Water-stress areas", "P6 · LI 2", f"Water-stress areas, withdrawal: {slabel}", "kL")
add("stress_total_water_withdrawal", P, G, "Water-stress areas", "P6 · LI 2", "Water-stress areas: total water withdrawal", "kL")
add("stress_total_water_consumption", P, G, "Water-stress areas", "P6 · LI 2", "Water-stress areas: total water consumption", "kL")
add("stress_water_intensity", P, G, "Water-stress areas", "P6 · LI 2", "Water-stress areas: water intensity per rupee of turnover", "kL/INR")
add("stress_total_water_discharged", P, G, "Water-stress areas", "P6 · LI 2", "Water-stress areas: total water discharged", "kL")
SUM_CHECKS["stress_total_water_withdrawal"] = [f"stress_water_{s}" for s in ["surface", "groundwater", "third_party", "seawater", "others"]]

add("scope3_emissions", P, G, "GHG emissions", "P6 · LI 3", "Total Scope 3 emissions", "tCO2e")
add("scope3_intensity_turnover", P, G, "GHG emissions", "P6 · LI 3", "Total Scope 3 emissions per rupee of turnover", "tCO2e/INR")
add("scope3_intensity_optional", P, G, "GHG emissions", "P6 · LI 3", "Total Scope 3 emission intensity (optional)", "as stated")
add("value_chain_env_assessed_pct", P, G, "Assessments", "P6 · LI 9",
    "% of value chain partners (by value of business) assessed for environmental impacts", "%")

# Not BRSR questions, but many reports give them in the energy notes
for f, flabel in [("coal", "Coal"), ("diesel", "Diesel / HSD"), ("petrol", "Petrol"), ("natural_gas", "Natural gas / PNG / CNG"),
                  ("lpg", "LPG"), ("furnace_oil", "Furnace oil / LDO"), ("biomass", "Biomass / biofuel")]:
    add(f"fuel_{f}", P, G, "Fuel (extra, if reported)", "Not a BRSR field", f"{flabel} consumed, if the report gives it", "as stated")

SUM_CHECKS.update({
    "renewable_energy_consumption": ["renewable_electricity", "renewable_fuel", "renewable_other"],
    "non_renewable_energy_consumption": ["non_renewable_electricity", "non_renewable_fuel", "non_renewable_other"],
    "total_energy_consumption": ["renewable_energy_consumption", "non_renewable_energy_consumption"],
    "total_water_withdrawal": [f"water_{s}" for s in ["surface", "groundwater", "third_party", "seawater", "others"]],
})
NOT_MORE_THAN += [("total_water_consumption", "total_water_withdrawal"),
                  ("total_water_discharged", "total_water_withdrawal"),
                  ("stress_total_water_withdrawal", "total_water_withdrawal")]

# =====================================================================================
# PRINCIPLES 8 and 9 - communities and consumers
# =====================================================================================
G, P = "p8_p9", "Social"
add("msme_sourcing_pct", P, G, "Community", "P8 · EI 4", "Input material directly sourced from MSMEs / small producers (% of total inputs by value)", "%")
add("india_sourcing_pct", P, G, "Community", "P8 · EI 4", "Input material directly from within India (% of total inputs by value)", "%")
for area, alabel in [("rural", "Rural"), ("semi_urban", "Semi-urban"), ("urban", "Urban"), ("metro", "Metropolitan")]:
    add(f"wages_{area}_pct", P, G, "Community", "P8 · EI 5",
        f"Wages paid to persons employed in {alabel} locations (% of total wage cost)", "%")
add("csr_aspirational_districts_amount", P, G, "Community", "P8 · LI 2", "Total CSR amount spent in aspirational districts", "INR")
add("preferential_procurement_pct", P, G, "Community", "P8 · LI 3(c)",
    "Preferential procurement from marginalised / vulnerable groups as % of total procurement (by value)", "%")
add("csr_beneficiaries_count", P, G, "Community", "P8 · LI 6", "Total no. of persons benefitted from CSR projects", "count")
add("csr_amount_spent", P, G, "Community", "Not a BRSR field", "Total CSR amount spent in the year, if the report gives it", "INR")
for key, desc in [("env_social_parameters", "Environmental and social parameters relevant to the product"),
                  ("safe_usage", "Safe and responsible usage"), ("recycling_disposal", "Recycling and/or safe disposal")]:
    add(f"product_info_{key}_pct", P, G, "Consumers", "P9 · EI 2",
        f"Turnover of products carrying information about {desc} (% of total turnover)", "%")
for topic, tlabel in [("data_privacy", "Data privacy"), ("advertising", "Advertising"), ("cyber_security", "Cyber-security"),
                      ("essential_services", "Delivery of essential services"), ("restrictive_trade", "Restrictive trade practices"),
                      ("unfair_trade", "Unfair trade practices"), ("other", "Other")]:
    add(f"consumer_complaints_{topic}_received", P, G, "Consumers", "P9 · EI 3", f"Consumer complaints, {tlabel}: received during the year", "count")
    add(f"consumer_complaints_{topic}_pending", P, G, "Consumers", "P9 · EI 3", f"Consumer complaints, {tlabel}: pending resolution at end of year", "count")
    NOT_MORE_THAN.append((f"consumer_complaints_{topic}_pending", f"consumer_complaints_{topic}_received"))
add("product_recalls_voluntary", P, G, "Consumers", "P9 · EI 4", "Instances of product recalls on account of safety issues: voluntary", "count")
add("product_recalls_forced", P, G, "Consumers", "P9 · EI 4", "Instances of product recalls on account of safety issues: forced", "count")
add("data_breaches_count", P, G, "Consumers", "P9 · EI 7", "Number of instances of data breaches", "count")
add("data_breaches_pii_pct", P, G, "Consumers", "P9 · EI 7", "% of data breaches involving personally identifiable information of customers", "%")

# =====================================================================================
# Requests to Claude: which pages to look at for each group
# =====================================================================================
GROUPS = {
    "section_a": dict(max_pages=15, keywords=[
        "paid-up", "paid up capital", "plants", "offices", "markets served", "export", "permanent", "other than permanent",
        "differently abled", "board of directors", "key management", "turnover rate", "csr", "net worth",
        "complaints", "grievance", "shareholders", "value chain partners"]),
    "p1_p2_p7": dict(max_pages=15, keywords=[
        "principle 1", "principle 2", "principle 7", "awareness programmes", "penalty", "fine", "settlement", "compounding",
        "bribery", "corruption", "conflict of interest", "accounts payable", "trading houses", "dealers", "distributors",
        "related part", "r&d", "capex", "sustainably", "recycled", "reclaim", "trade and industry", "chambers", "associations"]),
    "p3_benefits": dict(max_pages=12, keywords=[
        "principle 3", "health insurance", "accident insurance", "maternity", "paternity", "day care", "well-being",
        "wellbeing", "provident", "pf", "gratuity", "esi", "parental leave", "return to work", "retention", "unions", "associations"]),
    "p3_training_safety": dict(max_pages=12, keywords=[
        "principle 3", "health and safety", "skill upgradation", "career development", "performance", "ltifr", "lost time",
        "recordable", "fatalit", "high consequence", "permanent disabilit", "working conditions", "assessed", "rehabilitat"]),
    "p5": dict(max_pages=12, keywords=[
        "principle 5", "human rights", "minimum wage", "median", "remuneration", "gross wages", "sexual harassment", "posh",
        "discrimination", "child labour", "forced", "involuntary", "wages", "assessed"]),
    "p6": dict(max_pages=20, keywords=[
        "principle 6", "energy consumption", "electricity consumption", "fuel consumption", "renewable", "joules", " gj",
        "water withdrawal", "surface water", "groundwater", "third party water", "seawater", "water consumption", "kilolitre",
        "water discharge", "treatment", "water stress", "nox", "sox", "particulate", "scope 1", "scope 2", "scope 3", "tco2",
        "emission", "plastic waste", "e-waste", "bio-medical", "battery waste", "hazardous", "recycled", "re-used",
        "incineration", "landfill", "coal", "diesel", "hsd", "natural gas", "lpg", "furnace oil", "biomass"]),
    "p8_p9": dict(max_pages=12, keywords=[
        "principle 8", "principle 9", "msme", "small producers", "within india", "rural", "semi-urban", "urban",
        "metropolitan", "aspirational", "preferential procurement", "beneficiaries", "csr", "consumer complaints",
        "data privacy", "advertising", "cyber", "recall", "data breach", "personally identifiable"]),
}

# sanity: every check refers to real metrics
for _t, _ps in SUM_CHECKS.items():
    assert _t in METRICS and all(p in METRICS for p in _ps), _t
for _a, _b in NOT_MORE_THAN:
    assert _a in METRICS and _b in METRICS, (_a, _b)
assert {m["group"] for m in METRICS.values()} == set(GROUPS)
