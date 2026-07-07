from app.schemas.case import Case


THI = Case(
    id="thi",
    title="A Baby Referred for Low IgG",
    topic="Antibody Deficiency (Transient)",
    patient="10-month-old boy (Toms)",
    difficulty="Beginner",
    opening_clinical="A 10-month-old boy, Toms, is referred to the Immunology Department outpatient clinic following an incidental finding of low serum IgG on a blood test ordered by his paediatrician. He has had three episodes of acute otitis media in the past four months and one episode of bronchitis, all treated successfully with standard oral antibiotics. His growth is following the 25th centile. There is no history of severe infections, hospitalisation, skin abscesses, fungal infections, or failure to thrive. His father had frequent ear infections throughout infancy, described by his own family doctor as 'low antibodies that resolved by age 3–4.' His mother is present and anxious.",
    opening="You are seeing Toms, a 10-month-old boy, and his mother. She says: \"Our paediatrician sent us here because his IgG came back low on a blood test. He has had three ear infections in four months and one chest infection. She called us very worried and said he might have an immune problem. We are very anxious.\"",
    target_diagnosis="Transient Hypogammaglobulinaemia of Infancy (THI)",
    target_iuis="Predominantly antibody deficiency — unclassified/transient",
    red_flags=["ivig started for mild thi without indication", "xla not properly excluded"],
    parent_prompt="""You are the MOTHER of Toms, a 10-month-old boy referred for low IgG. You are anxious but the child is essentially well. Answer only what is asked.

HISTORY (reveal only when asked):
- Infections: Fine for first few months. From 6–7 months, one ear infection after another. Always gets better with antibiotics. No skin infections, no thrush.
- Father standard: My husband had ear infections constantly as a baby.
- Father deeper (ONLY if student asks specifically about father's antibody or immune testing): A doctor told his mother that his antibodies were low but he would grow out of it. And he did — completely fine by age 3–4. No problems since.
- Tonsils (if asked): The doctor always comments that his tonsils look nice and normal.
- Maternal males (if asked): No, nobody on my side has had similar problems.
- Vaccines: All vaccines given. No unusual reactions.
- Growth: Following the 25th centile. Paediatrician says weight is fine for now.
- No severe infections, no hospitalisation, no skin abscesses, no fungal infections, no systemic illness.

PHYSICAL EXAM (provide when asked):
- Weight 8.9 kg (25th centile)
- Tonsils: PRESENT and normal size
- Bilateral tympanic membrane dullness (otitis media with effusion)
- Small cervical lymph nodes (0.5–1 cm, normal for age)
- No hepatosplenomegaly, no rash, no candidiasis, no absent lymphoid tissue

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.""",
    lab_data={
        "immunoglobulins": "IgG: 2.1 g/L ↓ (below reference range for 10 months: 3.0–10.0 g/L). IgA: 0.08 g/L ↓ (reference 0.1–0.4 g/L). IgM: 0.45 g/L (NORMAL for age). IgE: <10 IU/mL (normal).",
        "CBC / full blood count": "WBC 8,200/µL (normal). Neutrophils 5,400/µL (normal). Lymphocytes 2,600/µL (normal for age). Haemoglobin 11.4 g/dL (normal). Platelets 310,000/µL (normal).",
        "CRP": "CRP 14 mg/L ↑ (mildly elevated — consistent with current ear infection).",
        "ESR": "ESR 18 mm/hr (normal).",
        "procalcitonin": "Procalcitonin 0.15 ng/mL (normal — not septic).",
        "blood biochemistry": "Sodium 139 mmol/L (normal). Potassium 4.3 mmol/L (normal). Urea 4.0 mmol/L (normal). Creatinine 22 µmol/L (normal for age). Glucose 5.2 mmol/L (normal). ALT 20 U/L (normal). AST 28 U/L (normal). Bilirubin 6 µmol/L (normal). Albumin 34 g/L (normal). Total protein 58 g/L (normal — note: total protein low-normal reflects physiologically lower immunoglobulins at this age).",
        "ear swab / culture": "Streptococcus pneumoniae (non-typeable) — moderate growth from middle ear aspirate.",
        "blood culture": "No growth.",
        "urinalysis": "Colour: yellow, clear. pH 6.5. Specific gravity 1.016. Protein: negative. Glucose: negative. Blood: negative. Leucocytes: negative. Nitrites: negative. No abnormality.",
        "chest X-ray": "No consolidation. Mildly prominent hilar lymph nodes — non-specific and age-appropriate.",
        "abdominal ultrasound": "Normal. No organomegaly. No lymphadenopathy.",
        "complement / C3 C4": "C3, C4, CH50: all normal.",
        "HIV test": "NEGATIVE.",
        "lymphocyte subsets / flow cytometry": "CD19+ B cells: PRESENT and NORMAL (12% of lymphocytes — appropriate absolute count for age). CD3+ T cells: Normal. CD4+ T cells: Normal. CD8+ T cells: Normal. NK cells: Normal. BTK protein expression on monocytes: PRESENT — 100% of expected expression.",
        "vaccine antibody titres": "Anti-PCV13 IgG: 0.15 µg/mL (protective threshold 0.35 µg/mL). Anti-tetanus IgG: 0.08 IU/mL (threshold 0.1 IU/mL).",
        "lateral neck X-ray": "Adenoid tissue PRESENT and normal size. Tonsillar shadow present. Lymphoid tissue intact.",
        "immunodeficiency gene panel": "No pathogenic variants identified in BTK, IGHM, IGLL1, or other primary agammaglobulinaemia genes. No genetic cause of immunodeficiency found.",
        "serial IgG follow-up": "IgG at 14 months: 3.2 g/L. IgG at 20 months: 5.8 g/L.",
    },
    exam_findings="Weight 8.9 kg (25th centile — tracking appropriately). Tonsils PRESENT and normal. Bilateral tympanic membrane dullness (otitis media with effusion). Small bilateral cervical nodes (0.5–1 cm, normal). No hepatosplenomegaly. No rash. No candidiasis. No absent lymphoid tissue.",
    model_diagnosis="Transient Hypogammaglobulinaemia of Infancy (THI)",
    model_management="Watchful waiting (no IVIG today — mild infections, growth maintained, B cells present). Prophylactic amoxicillin for recurrent otitis media. Repeat serum Ig every 3–4 months. Check vaccine antibody titres post-booster at 12 months. IVIG only if: ≥2 serious bacterial infections/year, invasive infection, or failure to thrive. If IgG still low at age 4 with absent vaccine responses → redefine as CVID.",
    model_genetic_counselling="THI has no single causative gene — polygenic/multifactorial. Father's history of 'low antibodies as an infant, resolved at age 3–4' is consistent with familial THI tendency. No X-linked risk: mother is not a BTK carrier. Future siblings: modestly elevated background risk of THI but no Mendelian recurrence risk. Key message: This is not the serious immunodeficiency that was feared. Toms almost certainly has the same benign pattern his father had.",
    key_clues=["Onset after 6 months (after maternal IgG wanes — same as XLA, but different mechanism)", "Infections mild — responding to standard antibiotics", "Tonsils PRESENT (unlike XLA)", "B cells PRESENT and normal on flow cytometry (excludes all agammaglobulinaemia)", "BTK normal (excludes XLA)", "Father had identical history resolving at age 3–4", "IgM preserved (T-independent responses maintained)"],
    wrong_paths={
        "xla": "XLA is the critical diagnosis to exclude here — both present with low IgG in a male infant after 6 months. The key distinction: B cells. In XLA, CD19+ B cells are completely ABSENT (0%). Here, B cells are PRESENT and NORMAL at 12%. BTK protein is also normal. XLA cannot coexist with normal B cells. What does this tell you about the diagnosis?",
        "start ivig immediately": "IVIG in mild THI is not evidence-based and may cause harm — it suppresses endogenous IgG production by feedback inhibition, potentially delaying natural resolution. Is there evidence of serious bacterial infections, invasive infection, or failure to thrive here? Infections are mild, growth is maintained, and B cells are present and maturing. What is the appropriate management for this severity?",
        "cvid": "CVID is a valid concern if low IgG persists — but at 10 months, it is far too early to diagnose CVID, which typically presents in the 2nd–3rd decade. CVID also requires persistent deficiency beyond age 4 with absent vaccine responses. What should the monitoring plan be?",
    },
)
