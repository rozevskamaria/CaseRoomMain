from app.schemas.case import Case


HIES = Case(
    id="hies",
    title="A Teenager Whose Eczema Never Responds to Treatment",
    topic="Combined Immunodeficiency",
    patient="13-year-old girl",
    difficulty="Advanced",
    opening_clinical="A 13-year-old girl is referred to the Immunology Department by her dermatologist. She has had chronic eczematous skin disease since infancy, attributed to atopic dermatitis in the context of her mother's asthma and hay fever. However, over the past 5 years she has had 3 episodes of pneumonia requiring hospitalisation, the most recent of which demonstrated a cavitary lesion on chest CT. She has also had 4–5 episodes of large skin abscesses draining Staphylococcus aureus, and persistent oral and nail candidiasis recurring shortly after each antifungal course. Her mother is present.",
    opening="You are seeing a 13-year-old girl and her mother in the immunology clinic. The mother says: \"She has had eczema since she was a baby. The dermatologist has tried everything. It never really goes away. And she keeps getting these big lumps under her arm and on her neck that have to be drained. The surgeons said it is always Staphylococcus. I thought it was connected to my asthma and allergies, but nobody can explain why it keeps happening.\"",
    target_diagnosis="Hyper-IgE Syndrome (STAT3 Loss-of-Function)",
    target_iuis="Combined immunodeficiency with associated/syndromic features",
    red_flags=["cold abscesses in child dismissed as atopy", "pneumatocele not monitored", "no antifungal prophylaxis"],
    parent_prompt="""You are the MOTHER of a 13-year-old girl with eczema and recurrent infections. You are worried but somewhat resigned to it being 'just allergy'. Answer only what is asked.

HISTORY (reveal only when asked):
- Skin swellings: Big soft lumps — 4 or 5 times drained. Cultures always Staphylococcus. "They were big but she barely complained about pain. That always seemed strange."
- Candidiasis: Mouth thrush keeps coming back. Even after antifungal treatment it returns.
- Pneumonia: Three hospitalisations for pneumonia. Last one had a cavity on the CT scan.
- Family: I have asthma and hay fever. Father completely healthy. No relatives with similar problems.
- If asked about whether swellings were painful: "They were soft, not very red, and she didn't have fever with most of them."
- If asked about IgE: "A doctor tested her IgE once — it came back very high. Over 2,000 they said."
- If asked about teeth: "She still has 4 baby teeth at age 13 — the dentist says they never fell out properly."
- If asked about scoliosis: "Mild scoliosis was found on X-ray last year."
- No history of abdominal abscesses or catalase-positive organisms beyond S. aureus.

PHYSICAL EXAM (provide when asked):
- Chronic lichenified eczematous plaques on antecubital/popliteal fossae, neck, face
- Dystrophic nails bilaterally
- White plaques on buccal mucosa (candidiasis)
- 4 retained deciduous teeth
- Healed scar from prior abscess drainage
- Mild thoracic scoliosis on inspection
- Normal tonsils

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.""",
    lab_data={
        "CBC / full blood count": "WBC 19,500/µL ↑. Neutrophils 11,800/µL ↑. Eosinophils 3,100/µL ↑↑. Lymphocytes 4,200/µL (normal). Haemoglobin 11.3 g/dL (mildly low). Platelets 380,000/µL (normal).",
        "CRP": "CRP 18 mg/L ↑ (mildly elevated — intercurrent skin infection).",
        "ESR": "ESR 28 mm/hr ↑ (mildly elevated).",
        "blood biochemistry": "Sodium 139 mmol/L (normal). Potassium 4.1 mmol/L (normal). Urea 5.2 mmol/L (normal). Creatinine 58 µmol/L (normal for age). Glucose 5.0 mmol/L (normal). ALT 18 U/L (normal). AST 22 U/L (normal). Bilirubin 9 µmol/L (normal). ALP 120 U/L (normal). Albumin 34 g/L (low-normal — chronic inflammatory skin disease). Total protein 62 g/L (normal).",
        "immunoglobulins": "IgG: 1,240 mg/dL (normal for age). IgA: 280 mg/dL (normal). IgM: 110 mg/dL (normal). IgE: >2,400 IU/mL ↑↑↑.",
        "complement / C3 C4": "C3, C4, CH50: all normal.",
        "skin swab / wound culture": "Staphylococcus aureus (MSSA) — heavy growth from abscess aspirate.",
        "blood culture": "No growth.",
        "throat swab": "Normal flora. No pathogen isolated.",
        "urinalysis": "Colour: yellow, clear. pH 6.2. Specific gravity 1.018. Protein: negative. Glucose: negative. Blood: negative. Leucocytes: negative. Nitrites: negative. No abnormality.",
        "chest X-ray": "Right lower lobe opacity — consistent with resolving pneumonia. No acute consolidation at present.",
        "chest CT": "Thin-walled pneumatocele in right lower lobe (2.1 cm). No active consolidation. No bronchiectasis.",
        "spine / skeletal X-ray": "Mild thoracic scoliosis (Cobb angle 14°). No fractures. Bone density mildly reduced for age.",
        "dental X-ray / OPG": "4 retained deciduous teeth at age 13 — permanent successors present but unable to erupt. No dental abscess.",
        "abdominal ultrasound": "No hepatosplenomegaly. Normal.",
        "lymphocyte subsets / flow cytometry": "CD3, CD4, CD8, B cells, NK cells: all within normal absolute counts. Th17 cells (CD4+CCR6+CXCR3−): MARKEDLY DECREASED (<0.5% of CD4+ cells — virtually absent). Th2 cells: elevated.",
        "cytokine panel / IL-17": "IL-17A: UNDETECTABLE (<1 pg/mL). IL-22: low (<4 pg/mL). IL-4: elevated. IL-10: elevated. TNF-α: normal. IFN-γ: normal.",
        "HIV test": "NEGATIVE.",
        "immunodeficiency gene panel": "Pathogenic variant identified: STAT3 gene, heterozygous c.1144C>T, p.R382W (DNA-binding domain, loss-of-function). De novo mutation confirmed — both parents tested negative.",
        "echocardiogram": "Normal cardiac structure and function. No coronary artery tortuosity detected at this assessment.",
    },
    exam_findings="Lichenified eczema on face, neck, antecubital and popliteal fossae. Dystrophic nails. White candidal plaques on buccal mucosa. 4 retained deciduous teeth (13 years old). Healed scar from abscess drainage on neck. Mild thoracic scoliosis. Normal tonsils. No hepatosplenomegaly.",
    model_diagnosis="Hyper-IgE Syndrome (Job Syndrome) — STAT3 loss-of-function, autosomal dominant, de novo",
    model_management="Prophylactic fluconazole (Candida, lifelong). Prophylactic TMP-SMX/cloxacillin (S. aureus). Annual chest CT (pneumatocele monitoring, Aspergillus risk). DEXA scan. Dental panoramic X-ray yearly (retained teeth). Echocardiogram every 2–3 years (coronary artery risk). Live vaccines NOT contraindicated.",
    model_genetic_counselling="De novo STAT3 LOF mutation — not inherited from either parent (both negative). Autosomal dominant. Risk to her own future children: 50%. Distinguish from STAT3 GOF (completely different syndrome). Genetic counselling and reproductive options available.",
    key_clues=["Cold abscesses — large, painless, non-inflammatory", "IgE >2,000 exceeds atopic range", "Retained primary teeth at age 13 (pathognomonic skeletal feature)", "Scoliosis (another skeletal feature)", "Absent Th17 cells and undetectable IL-17A", "Pneumatocele on chest CT", "De novo STAT3 LOF mutation"],
    wrong_paths={
        "atopy": "Severe atopy is a reasonable first thought given the family history and high IgE. However: atopic dermatitis does NOT cause cold abscesses (large, painless, non-inflammatory purulent lesions). It does NOT cause retained primary teeth or scoliosis. And IgE >2,000 is extreme even for very severe atopy. Which findings cannot be explained by atopy alone?",
        "cmc": "Chronic mucocutaneous candidiasis could explain the recurrent candidiasis — and absent Th17 cells are present in both CMC and HIES. However, CMC does not explain the cold S. aureus abscesses, pneumatocele, or skeletal features. The full syndrome points toward a broader STAT3 defect.",
        "cgd": "CGD causes deep S. aureus abscesses, but CGD abscesses are typically HOT and inflammatory, not cold. Also: no Serratia, no Aspergillus, no liver abscess; normal oxidative burst expected in HIES. What is the key functional T-cell defect here?",
    },
)
