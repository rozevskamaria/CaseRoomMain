from app.schemas.case import Case


CGD = Case(
    id="cgd",
    title="Emils — A Toddler With Abscesses Everywhere",
    topic="Phagocyte Defect",
    patient="3-year-old boy",
    difficulty="Advanced",
    opening_clinical="A 3-year-old boy, Emils, is referred to the Immunology Department by his surgeon following his third major surgical procedure for deep-seated abscesses. He has been described as 'always sick' since infancy. He required liver abscess drainage at age 1. He has had multiple recurrent perianal and axillary abscesses, chronically poor wound healing, and was treated for pulmonary aspergillosis last year. Notably, his full blood count has always shown a normal white cell count between infection episodes. His father is present and willing to answer questions.",
    opening="You are seeing Emils, a 3-year-old boy, with his father. The boy has been 'always sick' since infancy. The father says: \"He has had liver surgery at age 1 for an abscess. He keeps getting new abscesses — under his arm, near his bottom. Even small cuts get infected and take weeks to heal. He also had a lung fungus last year. His white blood cell count is always normal. I don't understand how that is possible if he keeps getting these infections.\"",
    target_diagnosis="X-linked Chronic Granulomatous Disease (CGD)",
    target_iuis="Defects of phagocyte number, function, or both",
    red_flags=["aspergillus not treated urgently", "bcg mentioned without contraindication noted", "no antifungal prophylaxis discussed"],
    parent_prompt="""You are the FATHER of Emils, a 3-year-old with recurrent infections. You are frustrated and worried. Answer only what is asked.

HISTORY (reveal only when asked):
- Infections: Always getting abscesses — armpit, near the bottom, once in the liver (needed surgery at age 1). Cultures grow Staphylococcus. ONCE the doctors said Serratia — they said that was very unusual.
- BCG: We were told not to give BCG at birth. The doctor who told us this knew our family.
- Family (only if asked about mother's side): My wife's sister's son had the same kind of infections. He had Aspergillus in his lungs. He was eventually diagnosed with the same condition we now suspect.
- Wound healing: Cuts take a very long time — weeks. They look infected for a long time.
- GI (only if asked): He has stomach pains and loose stools sometimes. The doctors are checking for gut problems.
- Lung fungus: It was Aspergillus. They treated him for a long time.
- Growth: He eats well but doesn't gain weight properly.
- No eczema, no thrush, no unusual T-cell signs.

PHYSICAL EXAM (provide only when student says they want to examine):
- Weight 11.8 kg (3rd centile), height 88 cm (10th centile)
- Multiple healing wounds with poor-quality granulation tissue
- Two active crusted lesions on right leg
- Bilateral cervical and inguinal lymphadenopathy (2–3 cm, firm, non-tender)
- Mild hepatosplenomegaly; surgical scar from liver drainage
- Perianal fistulous scar tissue
- Normal tonsils

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.""",
    lab_data={
        "CBC / full blood count": "WBC 9,800/µL (NORMAL). Neutrophils 6,200/µL (NORMAL). Lymphocytes 2,100/µL (normal). Haemoglobin 10.8 g/dL ↓ (mild anaemia of chronic disease). Platelets 428,000/µL ↑ (reactive thrombocytosis).",
        "CRP": "CRP 28 mg/L ↑ (mildly elevated — low-grade ongoing infection between acute episodes).",
        "ESR": "ESR 55 mm/hr ↑ (elevated — chronic inflammation).",
        "procalcitonin": "Procalcitonin 0.4 ng/mL (mildly elevated — low-grade chronic infection).",
        "blood biochemistry": "Sodium 138 mmol/L (normal). Potassium 4.2 mmol/L (normal). Urea 4.8 mmol/L (normal). Creatinine 32 µmol/L (normal for age). Glucose 4.9 mmol/L (normal). ALT 68 U/L ↑ (elevated — hepatic involvement from prior abscess). AST 52 U/L ↑. Bilirubin 12 µmol/L (normal). ALP 210 U/L ↑ (elevated — hepatic inflammation). Albumin 26 g/L ↓ (low — chronic illness and poor growth). Total protein 58 g/L (normal).",
        "blood culture": "No growth — taken between acute infective episodes.",
        "wound swab / abscess culture": "Perianal abscess swab: Serratia marcescens (moderate growth). NOTE: Serratia in a child is very unusual and clinically significant. Previous liver abscess (historical): Staphylococcus aureus (MSSA).",
        "sputum / BAL culture": "Aspergillus fumigatus — POSITIVE. Galactomannan index 3.8 (strongly positive — consistent with invasive aspergillosis). Moulds identified on direct microscopy.",
        "blood culture (acute episode)": "Staphylococcus aureus — POSITIVE during previous acute febrile episode.",
        "urinalysis": "Colour: yellow, clear. pH 6.0. Specific gravity 1.020. Protein: negative. Glucose: negative. Blood: negative. Leucocytes: negative. Nitrites: negative. No significant growth.",
        "chest X-ray": "Multiple bilateral pulmonary nodules. One 1.5 cm cavitary lesion in right lower lobe with surrounding haziness. Findings concerning for invasive fungal infection.",
        "chest CT": "Multiple bilateral consolidative nodules. 1.8 cm cavitary lesion with halo sign in right lower lobe — highly consistent with invasive pulmonary aspergillosis.",
        "abdominal CT / ultrasound": "Hepatic scarring from prior abscess (historical). Mild splenomegaly. Perianal fistulous changes. Mesenteric lymphadenopathy. No active abscess currently.",
        "immunoglobulins": "IgG: 18.4 g/L ↑↑ (markedly elevated). IgA: 3.2 g/L ↑. IgM: 1.8 g/L (normal). IgE: 48 IU/mL (normal).",
        "complement / C3 C4": "C3, C4, CH50: all normal. Complement pathway intact.",
        "lymphocyte subsets / flow cytometry": "CD3+ T cells: Normal. CD4+ T cells: Normal. CD8+ T cells: Normal. CD19+ B cells: Normal. NK cells: Normal. Lymphocyte proliferation assays: Normal.",
        "DHR oxidative burst test": "Patient: ABSENT oxidative burst — neutrophils fail to oxidise dihydrorhodamine 123 after PMA stimulation (0% of normal). DIAGNOSTIC FOR CGD. Mother: BIMODAL result — 50% positive / 50% negative populations.",
        "NBT test": "Neutrophils fail to reduce nitroblue tetrazolium to blue formazan (0% positive). Confirmatory for CGD.",
        "HIV test": "NEGATIVE.",
        "colonoscopy and biopsy": "Non-caseating granulomas in sigmoid colon with cobblestoning — CGD-associated colitis.",
        "immunodeficiency gene panel": "Pathogenic variant identified: CYBB gene (gp91phox), hemizygous c.676C>T, p.Q226X (nonsense mutation). Consistent with X-linked chronic granulomatous disease. gp91phox protein expression by flow cytometry: ABSENT.",
    },
    exam_findings="Emils is small — weight 3rd centile, height 10th centile. Poor-quality wound healing visible on legs. Bilateral lymphadenopathy (2–3 cm, firm). Mild hepatosplenomegaly. Perianal fistulous scar. Surgical scar on abdomen from liver drainage. Normal tonsils and oropharynx.",
    model_diagnosis="X-linked Chronic Granulomatous Disease (CGD)",
    model_management="Prophylactic TMP-SMX (lifelong, antibacterial). Prophylactic itraconazole/voriconazole (lifelong, antifungal). Treat active Aspergillus with voriconazole IV. IFN-γ therapy (SC 3×/week). Refer for allogeneic HSCT evaluation (curative). BCG permanently contraindicated.",
    model_genetic_counselling="X-linked recessive — CYBB on Xp21. Mother is obligate carrier (bimodal DHR confirmed). 25% risk per pregnancy of affected son. Maternal aunt testing recommended. PGT/prenatal diagnosis available. BCG must never be given to males in this family before CGD is excluded.",
    key_clues=["Normal neutrophil COUNT but recurrent serious infections = qualitative defect", "Serratia marcescens virtually pathognomonic for CGD", "Aspergillus is the most dangerous CGD pathogen", "BCG withheld — family knew risk", "Absent oxidative burst on DHR test", "Maternal nephew with same condition"],
    wrong_paths={
        "lad": "LAD (Leukocyte Adhesion Deficiency) causes poor wound healing too, but LAD typically shows extreme leukocytosis (WBC >30,000) even when not infected, and does not cause Aspergillus infections. What does the neutrophil COUNT show here?",
        "hies": "HIES (Hyper-IgE Syndrome) also causes S. aureus abscesses, but HIES does not cause liver abscesses, Aspergillus, or Serratia. Also: no eczema, normal IgE. What is the single most important functional test for neutrophils?",
        "cvid": "CVID causes antibody deficiency — but here IgG is ELEVATED (from chronic infection), not low. This pattern suggests a phagocyte defect. What does the lymphocyte subset profile tell you?",
    },
)
