from app.schemas.case import Case


PFAPA = Case(
    id="pfapa",
    title="A Girl With Predictable Monthly Fevers",
    topic="Autoinflammatory",
    patient="3-year-old girl",
    difficulty="Intermediate",
    opening_clinical="A 3-year-old girl is referred to the Immunology/Rheumatology outpatient clinic with a 14-month history of recurrent febrile episodes. Her mother has kept a fever diary documenting 16 episodes over this period. Each episode lasts 4–6 days and recurs every 3–5 weeks with striking regularity. Between episodes the child is reported to be entirely well. Both parents are from Azerbaijan and are distant relatives (third cousins). MEFV gene sequencing was ordered previously due to ethnic background and has returned negative for pathogenic variants. Her mother is present with the fever diary.",
    opening="You are seeing a 3-year-old girl and her mother. The mother says: \"She has been getting high fevers since she was one year old. Every 4 or 5 weeks, like clockwork. During the fever she gets a sore throat and swollen neck glands. Then after 4 or 5 days it is completely gone. We are from Azerbaijan — my husband and I are distant relatives, third cousins. The doctors tested her for Mediterranean fever because of our background. The result came back completely negative.\"",
    target_diagnosis="PFAPA Syndrome",
    target_iuis="Autoinflammatory disorder (not an immunodeficiency)",
    red_flags=["fever attributed to infection without workup", "colchicine started without clinical indication"],
    parent_prompt="""You are the MOTHER of a 3-year-old girl with recurrent fevers. You and your husband are from Azerbaijan and are distant relatives (third cousins). Answer only what is asked.

HISTORY (reveal only when asked):
- Fever pattern: Exactly 4–5 days, always. Every 4–5 weeks, like clockwork. 16 episodes in 14 months. I keep a diary.
- Between episodes: She is 100% normal — running, eating, completely healthy.
- Symptoms during fever: High fever up to 40°C. Sore throat. Neck glands swollen. Small mouth sores on inner lip.
- Antibiotics: We always get antibiotics. She gets better on day 4–5 whether she takes them or not.
- Steroids (only if asked): Once a doctor gave her a steroid tablet — the fever was gone within 4–5 hours! But then the next episode came 3 weeks later instead of 5. Earlier than usual.
- FMF testing: They tested for Mediterranean fever because we are from Azerbaijan. The result was completely negative.
- Family (only if asked about mother's childhood): Actually I had something similar — fevers every month when I was small. I outgrew it around age 8.
- Abdominal pain (if asked): No stomach pain at all. No chest pain. Just throat and neck glands.
- No skin infections, no skin abscesses, no fungal infections.

PHYSICAL EXAM during fever episode (provide when asked):
- Temperature 40.1°C
- Bilateral tender cervical nodes (largest 2 cm)
- Mildly erythematous pharynx, NO exudate, NO pus
- Two small aphthous ulcers on inner lower lip
- No rash, no arthritis, no hepatosplenomegaly, no abdominal tenderness

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.""",
    lab_data={
        "CBC / full blood count": "WBC 15,200/µL ↑ (neutrophilia — during episode). Neutrophils 10,800/µL ↑. Lymphocytes 3,100/µL (normal). Eosinophils: normal. Platelets 445,000/µL ↑ (reactive thrombocytosis).",
        "CRP": "CRP 52 mg/L ↑ (elevated during fever episode).",
        "ESR": "ESR 38 mm/hr ↑ (elevated during episode).",
        "procalcitonin": "Procalcitonin 0.08 ng/mL — NORMAL.",
        "blood culture": "No growth — taken during acute episode.",
        "throat swab / rapid strep test": "Group A Streptococcus: NEGATIVE. No bacterial pathogen isolated. Rapid strep antigen test: negative.",
        "throat PCR / viral panel": "EBV: negative. CMV: negative. Adenovirus: negative. HHV-6: negative. Influenza A/B: negative. No viral pathogen detected.",
        "monospot / EBV serology": "Monospot: negative. EBV IgM: negative. EBV IgG: positive (prior infection, not acute).",
        "immunoglobulins": "IgG: 820 mg/dL (normal). IgA: 62 mg/dL (normal). IgM: 110 mg/dL (normal). IgE: 18 IU/mL (normal). IgD: 9 mg/dL (NORMAL).",
        "complement / C3 C4": "C3, C4, CH50: all normal.",
        "lymphocyte subsets / flow cytometry": "All T, B, NK cell populations: normal absolute counts.",
        "blood biochemistry": "Sodium 140 mmol/L (normal). Potassium 4.0 mmol/L (normal). Urea 4.5 mmol/L (normal). Creatinine 40 µmol/L (normal for age). Glucose 5.1 mmol/L (normal). ALT 22 U/L (normal). AST 25 U/L (normal). Bilirubin 7 µmol/L (normal). ALP 180 U/L (normal for age). Albumin 38 g/L (normal). Total protein 68 g/L (normal). NOTE: All parameters within normal limits during febrile episode.",
        "urinalysis": "Colour: yellow, clear. pH 6.5. Specific gravity 1.015. Protein: negative. Glucose: negative. Blood: negative. Leucocytes: negative. Nitrites: negative. No abnormality detected.",
        "ferritin": "Ferritin 110 ng/mL ↑ (mildly elevated during episode).",
        "abdominal ultrasound": "Normal. No organomegaly. No abdominal lymphadenopathy.",
        "chest X-ray": "Normal. No pulmonary infiltrate.",
        "autoinflammatory gene panel / MEFV": "MEFV gene sequencing (exons 1–10): No pathogenic variants detected on either allele. NEGATIVE for FMF-causing mutations. TNFRSF1A (TRAPS): no pathogenic variant. MVK (HIDS/MKD): no pathogenic variant.",
        "HIV test": "NEGATIVE.",
        "cytokine panel": "IL-1β: 42 pg/mL ↑. IL-18: 620 pg/mL ↑↑. IL-6: 38 pg/mL ↑.",
    },
    exam_findings="Temperature 40.1°C. Bilateral tender cervical lymph nodes, largest 2 cm. Erythematous pharynx — NO exudate, no pus. Two small aphthous ulcers on inner lower lip. No rash, no arthritis, no hepatosplenomegaly, no abdominal tenderness. Child is alert, not toxic-looking.",
    model_diagnosis="PFAPA Syndrome (Periodic Fever, Aphthous stomatitis, Pharyngitis, Adenitis)",
    model_management="Episodic prednisolone 1 mg/kg at fever onset — aborts episode in hours. Warn: steroids shorten inter-episode interval. Consider tonsillectomy (curative ~85–90%) if episodes ≥monthly. Anakinra (anti-IL-1) for refractory cases. MEFV negative — no indication for colchicine.",
    model_genetic_counselling="PFAPA has no single causative gene — polygenic/multifactorial. MEFV sequencing is negative for pathogenic variants. Family should understand: this is NOT FMF. Azerbaijani background appropriately triggered testing, but the negative result combined with non-FMF clinical features excludes FMF. Excellent prognosis — spontaneous resolution expected before adolescence.",
    key_clues=["Perfect periodicity every 4–5 weeks", "Complete wellness between episodes", "Pharyngitis + aphthous ulcers + cervical adenitis = classic PFAPA triad", "No serositis — rules out FMF", "MEFV sequencing negative", "Rapid steroid response (hours) is near-diagnostic", "Maternal history of same condition resolving at age 8"],
    wrong_paths={
        "fmf": "FMF is a valid concern given the Azerbaijani background — ordering MEFV testing was correct clinical reasoning. However, MEFV sequencing is completely negative for pathogenic variants. Also: FMF episodes last 1–3 days (not 4–6), and FMF requires serositis — abdominal pain, pleuritis. Neither is present here. What does this tell you?",
        "traps": "TRAPS causes periodic fevers too, but TRAPS episodes typically last over 7 days or even weeks, with periorbital oedema and migratory myalgia — all absent here. TNFRSF1A gene is also normal.",
        "bacterial tonsillitis": "Recurrent bacterial tonsillitis is possible, but: all infectious PCRs are negative, procalcitonin is normal, the pattern is perfectly regular (not random), and the fever resolves on day 4–5 regardless of antibiotics. What does the steroid response tell you?",
    },
)
