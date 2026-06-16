from app.schemas.case import Case


XLA = Case(
    id="xla",
    title="A Boy Who Is Always Getting Pneumonia",
    topic="Antibody Deficiency",
    patient="2-year-old boy",
    difficulty="Intermediate",
    opening_clinical="A 2-year-old boy is referred to the Immunology Department outpatient clinic by his paediatrician. The referral letter states: recurrent bacterial infections since approximately 6 months of age, including two episodes of pneumonia requiring hospitalisation and multiple courses of antibiotics for sinusitis and otitis media. The child was healthy as an infant prior to this age. Growth has been poor, with weight falling below the 5th centile. His mother is present and willing to answer questions.",
    opening="You are seeing a 2-year-old boy and his mother. She was referred by her paediatrician because her son has been getting pneumonia repeatedly and always needs antibiotics or hospitalisation. She looks worried and says: \"He used to be healthy as a baby, but since about seven months old he has been getting one infection after another. I don't know why.\"",
    target_diagnosis="X-linked Agammaglobulinaemia (XLA)",
    target_iuis="Predominantly antibody deficiency",
    red_flags=["live vaccines given", "no B cells mentioned without prophylaxis", "bacteraemia not treated urgently"],
    parent_prompt="""You are the MOTHER of a 2-year-old boy with recurrent bacterial infections. You are worried but calm. Answer only what is asked. Do not volunteer information unless it is your opening complaint.

HISTORY (reveal only when asked):
- Onset: Infections started around 6–7 months old. Before that he was healthy.
- Infections: Ear infections constantly. Two pneumonias needing hospital. Sinusitis and bronchitis needing antibiotics. Always bacteria — Streptococcus, Haemophilus.
- Vaccines: All vaccines given. He had the rotavirus drops at 2 months. He had terrible diarrhoea for 4 weeks after that. We thought it was a bug.
- Tonsils (only if asked): The ENT doctor said he has no tonsils at all. He could never find them.
- Maternal family (CRITICAL — only if student asks about males on mother's side or unexplained deaths): My brother died at age 3 in 1989. They said it was overwhelming pneumonia but nobody explained why. He was always sick as a baby.
- Stool: He has some loose stools sometimes. We thought it was normal.
- Growth: He is thin. The paediatrician says his weight is low.
- No fungal infections, no skin abscesses, no unusual organisms.

PHYSICAL EXAM (provide only when student says they want to examine):
- No visible tonsils
- No palpable lymph nodes anywhere
- Bilateral tympanic membrane retraction (chronic otitis media)
- Weight below 5th centile
- No hepatosplenomegaly, no rash, no candidiasis

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.""",
    lab_data={
        "CBC / full blood count": "WBC 6,200/µL (normal). Neutrophils 4,500/µL (normal). Lymphocytes 1,200/µL ↓ (low for age — reference 2,000–8,000). Monocytes normal. Haemoglobin 11.8 g/dL (mildly low). Platelets 320,000/µL (normal). MCV 78 fL (normal).",
        "CRP": "CRP 84 mg/L ↑ (elevated — active bacterial infection).",
        "ESR": "ESR 42 mm/hr ↑ (elevated).",
        "procalcitonin": "Procalcitonin 2.8 ng/mL ↑↑ (elevated — consistent with bacterial infection).",
        "blood biochemistry": "Sodium 137 mmol/L (normal). Potassium 4.1 mmol/L (normal). Urea 4.2 mmol/L (normal). Creatinine 28 µmol/L (normal for age). Glucose 4.8 mmol/L (normal). ALT 28 U/L (normal). AST 22 U/L (normal). Bilirubin 8 µmol/L (normal). ALP 145 U/L (normal for age). Albumin 28 g/L ↓ (low — chronic illness and malnutrition). Total protein 52 g/L ↓ (low — reflects absent immunoglobulin contribution).",
        "blood culture": "Streptococcus pneumoniae — POSITIVE (bacteraemia confirmed). Susceptible to penicillin.",
        "urinalysis": "Colour: yellow, clear. pH 6.2. Specific gravity 1.018. Protein: negative. Glucose: negative. Blood: negative. Leucocytes: negative. Nitrites: negative. Ketones: trace. No significant growth on culture.",
        "throat swab": "Haemophilus influenzae (non-typeable) — moderate growth.",
        "ear swab": "Streptococcus pneumoniae — moderate growth (consistent with acute otitis media).",
        "chest X-ray": "Bilateral lower lobe consolidation consistent with pneumonia. No pleural effusion. No cavitary lesion. No pneumatocele.",
        "chest CT": "Bilateral lower lobe consolidation. No pneumatocele or cavitary lesion. No bronchiectasis. Mildly prominent hilar nodes — reactive.",
        "abdominal ultrasound": "No hepatosplenomegaly. Normal-sized liver and spleen. No abdominal lymphadenopathy. Normal bowel.",
        "immunoglobulins": "IgG: <100 mg/dL ↓↓↓ (severely decreased; normal for age >400 mg/dL). IgA: <5 mg/dL (UNDETECTABLE). IgM: <10 mg/dL ↓↓↓ (severely decreased). IgE: <2 IU/mL (absent). Total protein: 42 g/L ↓↓ (low — reflects absent immunoglobulin contribution).",
        "complement / C3 C4": "C3: 1.4 g/L (normal). C4: 0.28 g/L (normal). CH50: normal.",
        "lymphocyte subsets / flow cytometry": "CD3+ T cells: Normal absolute count. CD4+ T cells: Normal. CD8+ T cells: Normal. CD19+ B cells: ABSENT (0.0%) ↓↓↓ — complete absence of B lymphocytes. NK cells: Normal. BTK protein expression on monocytes: ABSENT.",
        "vaccine antibody titres": "Anti-pneumococcal IgG: undetectable (<0.1 µg/mL). Anti-tetanus IgG: undetectable. Anti-Hib IgG: undetectable.",
        "stool examination": "Giardia lamblia cysts: POSITIVE (moderate load). No other parasites. No bacterial pathogen isolated.",
        "HIV test": "HIV 1/2 antibody: NEGATIVE.",
        "ferritin": "Ferritin 18 ng/mL ↓ (low — consistent with iron deficiency from poor nutrition).",
        "immunodeficiency gene panel": "Pathogenic variant identified: BTK gene, hemizygous c.1684C>T, p.R562C (kinase domain, loss of function). Classified as pathogenic. Consistent with X-linked agammaglobulinaemia.",
        "skin prick test / allergy test": "Not performed.",
        "ECG": "Normal sinus rhythm. No abnormality.",
    },
    exam_findings="The boy is thin, weight below 5th centile. No visible tonsils — the pharynx is bare. No palpable lymph nodes in the neck, axillae, or groin. Bilateral tympanic membranes dull and retracted. No hepatosplenomegaly. No rash, no candidiasis. Normal neurological examination.",
    model_diagnosis="X-linked Agammaglobulinaemia (XLA)",
    model_management="Start IVIG/SCIG immediately (IgG trough target ≥8 g/L). Treat Giardia with metronidazole. Treat bacteraemia with IV antibiotics. Permanently contraindicate all live vaccines. Long-term: pulmonary surveillance, Giardia screening, IVIG lifelong.",
    model_genetic_counselling="X-linked recessive — BTK on Xq22. Mother is obligate carrier. Each son: 25% affected. Carrier testing for maternal aunts. Prenatal diagnosis/PGT available. Maternal uncle almost certainly had XLA.",
    key_clues=["Infections started at 6–7 months (after maternal IgG wanes)", "Only bacterial infections — no fungi, no viruses", "No tonsils on examination", "Maternal uncle died of 'overwhelming pneumonia' at age 3", "Absent B cells on flow cytometry", "All immunoglobulins severely decreased"],
    wrong_paths={
        "cvid": "CVID is a valid consideration, but it typically presents in the 2nd–3rd decade, not at 2 years. Compare the B-cell count — in CVID, B cells are usually present. Here they are completely absent. Which diagnosis better explains absent B cells with very early onset?",
        "thi": "Transient hypogammaglobulinaemia of infancy (THI) is a good thought, but THI has PRESENT B cells and usually causes mild infections only. Here B cells are completely absent and infections are severe. Does THI fit the severity and the absent B cells?",
        "cgd": "CGD causes deep abscesses and catalase-positive infections — this child has encapsulated bacterial pneumonias, which are an antibody-deficiency pattern. What does the B-cell count tell you?",
    },
)
