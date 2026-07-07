from app.schemas.case import Case


SCID = Case(
    id="scid",
    title="A Baby With Infections After BCG Vaccination",
    topic="SCID / Combined Immunodeficiency",
    patient="Male infant, 2.5 months old",
    difficulty="Advanced",
    opening_clinical="A 2.5-month-old male infant is admitted to the Immunology Department from a regional hospital. He presented with erythroderma, a widespread maculopapular rash covering the trunk and extremities, and pneumonia with acute bronchiolitis. His mother reports that he appeared healthy at birth and was discharged on day 3 of life. BCG vaccination was delayed to 2 months of age due to parental hesitancy. The rash appeared shortly after BCG vaccination. He subsequently developed pneumonia and a bacterial skin infection. He has been hospitalised continuously since age 2.5 months. This is the family's first child; parents are non-consanguineous with no known family history of immunodeficiency.",
    opening="You are seeing a 2.5-month-old male infant and his mother in hospital. The baby was admitted with erythroderma, a maculopapular rash all over his body, and pneumonia. His mother says: \"He seemed healthy when he was born. We delayed the tuberculosis vaccine until he was two months old because we had some worries. Shortly after he got it, he developed this rash all over his body. Then he started getting chest infections. He has been in hospital ever since. The doctors say his immune system may not be working.\"",
    target_diagnosis="SCID — Artemis deficiency (DCLRE1C), T⁻B⁻NK⁺, complicated by maternal T-cell engraftment",
    target_iuis="Combined T and B cell immunodeficiency",
    red_flags=["live vaccines not immediately contraindicated", "no urgent HSCT referral", "bcg disease not treated", "no isolation precautions mentioned"],
    parent_prompt="""You are the MOTHER of a 2.5-month-old male infant who has been very sick since shortly after BCG vaccination. You are frightened. Answer only what is asked.

HISTORY (reveal only when asked):
- BCG timing: We delayed it to 2 months because we had read some things online that worried us.
- Rash: It appeared shortly AFTER the BCG vaccine. All over his body. It has not improved.
- Infections: Pneumonia, chest infections, a bacterial skin infection (S. aureus and Streptococcus viridans).
- BCG arm (only if student directly asks): There is a sore on his arm where the vaccine was given. It is not healing. His armpit on that side is swollen.
- Breastfeeding: Only for one month.
- Family: We are not related. No family history of immune problems. This is our first child.
- Other vaccines: No other vaccines after BCG.
- Stool MTB (only if student asks about tuberculosis spread): They tested his stool and found tuberculosis DNA in it. The doctors said the BCG vaccine may be spreading through his body.
- No family history of similar illness, no consanguinity.

PHYSICAL EXAM (provide when asked):
- Erythroderma with widespread maculopapular rash
- Oral candidiasis
- Signs of acute bronchiolitis (wheeze, accessory muscle use)
- No palpable lymph nodes
- Tonsils present (normal size)
- No hepatosplenomegaly at this point
- BCG injection site: cyanotic induration 10mm, left axillary lymphadenopathy

PATIENT WORSENING (if student has not mentioned live vaccines, isolation, or urgent referral by time they start ordering tests):
Say: "Doctor, I am worried — he seems more tired today and has developed a fever again. The rash is spreading. Is it safe for us to go home?"

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.""",
    lab_data={
        "CBC / full blood count": "WBC 6.16 × 10³/µL (near lower normal limit). ABSOLUTE LYMPHOCYTE COUNT: 1.44 × 10³/µL ↓↓↓ (reference 2.45–8.89 × 10³/µL). Eosinophils 2.20 × 10³/µL ↑↑ (35.7%). Monocytes 14.9% ↑. Platelets 779 × 10³/µL ↑.",
        "CRP": "CRP 68 mg/L ↑ (elevated — active infection).",
        "procalcitonin": "Procalcitonin 4.2 ng/mL ↑↑ (significantly elevated — bacterial co-infection).",
        "blood biochemistry": "Sodium 131 mmol/L ↓ (low — hyponatraemia, multifactorial). Potassium 4.8 mmol/L (normal). Urea 3.2 mmol/L (normal for age). Creatinine 18 µmol/L (normal for age). Glucose 4.2 mmol/L (normal). ALT 42 U/L ↑ (mildly elevated). AST 38 U/L ↑. Bilirubin 14 µmol/L (mildly elevated). Albumin 22 g/L ↓↓ (severely low — malnutrition and critical illness). Total protein 44 g/L ↓↓ (very low — malnutrition, absent immunoglobulins).",
        "blood culture": "Staphylococcus aureus (MSSA) and Streptococcus viridans — both isolated (polymicrobial bacteraemia).",
        "urinalysis": "Colour: yellow, concentrated. pH 5.8. Specific gravity 1.025. Protein: trace (concentrated urine — not clinically significant). Glucose: negative. Blood: negative. Leucocytes: negative. Nitrites: negative. No significant abnormality.",
        "throat swab": "Candida albicans — moderate growth (oral candidiasis confirmed).",
        "skin swab": "Staphylococcus aureus — isolated from skin lesions.",
        "stool culture / MTB PCR": "Mycobacterium tuberculosis DNA: POSITIVE in stool. Gastric lavage: negative.",
        "chest X-ray": "Diffuse bilateral interstitial opacification. Perihilar haziness. No thymic shadow visible (thymic aplasia — consistent with T-cell deficiency).",
        "chest CT": "Bilateral ground-glass opacification and interstitial infiltrates. Absent thymic shadow. No cavitary lesion.",
        "abdominal ultrasound": "Normal liver and spleen. No organomegaly at this assessment.",
        "immunoglobulins": "IgA: <0.00 g/L (UNDETECTABLE). IgG: 0.32 g/L ↓↓↓ (severely decreased; reference 2.32–14.11 g/L). IgM: 0.01 g/L ↓↓↓ (nearly absent). All immunoglobulin classes severely depleted.",
        "complement / C3 C4": "C3, C4: normal. Complement pathway intact.",
        "lymphocyte subsets / flow cytometry": "CD3+ T cells: 54% — absolute count 764/µL ↓↓↓ (reference 2,300–6,500/µL). CD8+ T cells: 0.79% / 11/µL ↓↓↓. CD4+ T cells: 52.9% / 748/µL ↓↓↓. B cells (CD19+): 1.83% / 26/µL ↓↓↓. NK cells: 42.2% / 598/µL. CD4/CD8 ratio: 67.3 (reference 1.7–3.9).",
        "HIV test": "HIV 1/2 antibody: NEGATIVE.",
        "TREC assay": "TRECs: very low / absent.",
        "chimerism testing / QF-PCR": "15% female (XX) cells detected in blood. QF-PCR confirms maternal origin.",
        "immunodeficiency gene panel": "Pathogenic variant identified: DCLRE1C gene (Artemis), homozygous deletion chr10:g.14945090_15021878del (exons 1–3). Artemis protein absent. T⁻B⁻NK⁺ SCID confirmed. Both parents are obligate heterozygous carriers.",
        "skin biopsy": "Psoriasiform hyperplasia, parakeratosis, spongiosis, necrotic keratinocytes, lichenoid infiltrate.",
    },
    exam_findings="Widespread erythroderma and maculopapular rash. Oral candidiasis. Accessory muscle use and wheeze consistent with bronchiolitis. NO palpable lymph nodes. Tonsils present. BCG injection site: 10mm cyanotic induration. Left axillary lymphadenopathy. No hepatosplenomegaly at this time.",
    model_diagnosis="Artemis-deficient SCID (DCLRE1C null variant) — T⁻B⁻NK⁺ phenotype with maternal T-cell engraftment and disseminated BCGitis",
    model_management="IMMEDIATE: (1) Protective isolation. (2) All live vaccines permanently contraindicated. (3) Start antimycobacterial therapy (ethambutol + levofloxacin + rifampicin). (4) IVIG for hypogammaglobulinaemia. (5) TMP-SMX prophylaxis (Pneumocystis). URGENT HSCT referral — SCID is universally fatal without transplant. Monitor for rifampicin–cyclosporine A drug interaction post-HSCT.",
    model_genetic_counselling="Autosomal recessive — DCLRE1C. Both parents are obligate carriers. 25% recurrence risk per pregnancy. Prenatal diagnosis/PGT available. Radiosensitivity — minimise ionising radiation lifelong. BCG must not be given to any future sibling before SCID is excluded. TREC newborn screening now available in Latvia (since April 1, 2023).",
    key_clues=["BCG vaccination → erythroderma = SCID alarm signal", "Critically low ABSOLUTE lymphocyte count (not just percentage)", "Virtually absent CD8+ cells", "Severely absent B cells", "Maternal T-cell engraftment masking the diagnosis (CD3% appears normal)", "Disseminated BCGitis confirmed by stool MTB PCR", "DCLRE1C null variant — Artemis deficiency"],
    wrong_paths={
        "omenn": "Omenn syndrome is an important differential — both cause erythroderma, eosinophilia, and circulating T cells. Key distinction: Omenn T cells are AUTOLOGOUS (patient's own autoreactive cells from hypomorphic mutations) and typically show markedly elevated IgE. Here, T cells are MATERNAL (allogeneic), IgE is very low, and chimerism studies confirm maternal origin. How would you distinguish these?",
        "atopy": "Atopic dermatitis cannot explain IgG 0.32 g/L, virtually absent B cells, absent CD8+ cells, or a critically low absolute lymphocyte count. The combination of severe rash + after BCG + profoundly low lymphocytes points to a life-threatening immunodeficiency.",
        "cvid": "CVID typically presents in the 2nd–3rd decade, not at 2.5 months. Also: the absolute lymphocyte count is critically low and CD8+ cells are virtually absent — CVID does not cause this pattern in infancy.",
    },
)
