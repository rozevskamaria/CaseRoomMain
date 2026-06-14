import { useState, useRef, useEffect } from "react";

// ── CASE LIBRARY ──────────────────────────────────────────────────────────────
const CASES = [
  {
    id: "xla", title: "A Boy Who Is Always Getting Pneumonia", topic: "Antibody Deficiency",
    patient: "2-year-old boy", difficulty: "Intermediate",
    openingClinical: "A 2-year-old boy is referred to the Immunology Department outpatient clinic by his paediatrician. The referral letter states: recurrent bacterial infections since approximately 6 months of age, including two episodes of pneumonia requiring hospitalisation and multiple courses of antibiotics for sinusitis and otitis media. The child was healthy as an infant prior to this age. Growth has been poor, with weight falling below the 5th centile. His mother is present and willing to answer questions.",
    opening: "You are seeing a 2-year-old boy and his mother. She was referred by her paediatrician because her son has been getting pneumonia repeatedly and always needs antibiotics or hospitalisation. She looks worried and says: \"He used to be healthy as a baby, but since about seven months old he has been getting one infection after another. I don't know why.\"",
    targetDiagnosis: "X-linked Agammaglobulinaemia (XLA)",
    targetIUIS: "Predominantly antibody deficiency",
    redFlags: ["live vaccines given", "no B cells mentioned without prophylaxis", "bacteraemia not treated urgently"],
    parentPrompt: `You are the MOTHER of a 2-year-old boy with recurrent bacterial infections. You are worried but calm. Answer only what is asked. Do not volunteer information unless it is your opening complaint.

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

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.`,
    labData: {
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
    examFindings: "The boy is thin, weight below 5th centile. No visible tonsils — the pharynx is bare. No palpable lymph nodes in the neck, axillae, or groin. Bilateral tympanic membranes dull and retracted. No hepatosplenomegaly. No rash, no candidiasis. Normal neurological examination.",
    modelDiagnosis: "X-linked Agammaglobulinaemia (XLA)",
    modelManagement: "Start IVIG/SCIG immediately (IgG trough target ≥8 g/L). Treat Giardia with metronidazole. Treat bacteraemia with IV antibiotics. Permanently contraindicate all live vaccines. Long-term: pulmonary surveillance, Giardia screening, IVIG lifelong.",
    modelGeneticCounselling: "X-linked recessive — BTK on Xq22. Mother is obligate carrier. Each son: 25% affected. Carrier testing for maternal aunts. Prenatal diagnosis/PGT available. Maternal uncle almost certainly had XLA.",
    keyClues: ["Infections started at 6–7 months (after maternal IgG wanes)", "Only bacterial infections — no fungi, no viruses", "No tonsils on examination", "Maternal uncle died of 'overwhelming pneumonia' at age 3", "Absent B cells on flow cytometry", "All immunoglobulins severely decreased"],
    wrongPaths: {
      "cvid": "CVID is a valid consideration, but it typically presents in the 2nd–3rd decade, not at 2 years. Compare the B-cell count — in CVID, B cells are usually present. Here they are completely absent. Which diagnosis better explains absent B cells with very early onset?",
      "thi": "Transient hypogammaglobulinaemia of infancy (THI) is a good thought, but THI has PRESENT B cells and usually causes mild infections only. Here B cells are completely absent and infections are severe. Does THI fit the severity and the absent B cells?",
      "cgd": "CGD causes deep abscesses and catalase-positive infections — this child has encapsulated bacterial pneumonias, which are an antibody-deficiency pattern. What does the B-cell count tell you?",
    }
  },
  {
    id: "cgd", title: "Emils — A Toddler With Abscesses Everywhere", topic: "Phagocyte Defect",
    patient: "3-year-old boy", difficulty: "Advanced",
    openingClinical: "A 3-year-old boy, Emils, is referred to the Immunology Department by his surgeon following his third major surgical procedure for deep-seated abscesses. He has been described as 'always sick' since infancy. He required liver abscess drainage at age 1. He has had multiple recurrent perianal and axillary abscesses, chronically poor wound healing, and was treated for pulmonary aspergillosis last year. Notably, his full blood count has always shown a normal white cell count between infection episodes. His father is present and willing to answer questions.",
    opening: "You are seeing Emils, a 3-year-old boy, with his father. The boy has been 'always sick' since infancy. The father says: \"He has had liver surgery at age 1 for an abscess. He keeps getting new abscesses — under his arm, near his bottom. Even small cuts get infected and take weeks to heal. He also had a lung fungus last year. His white blood cell count is always normal. I don't understand how that is possible if he keeps getting these infections.\"",
    targetDiagnosis: "X-linked Chronic Granulomatous Disease (CGD)",
    targetIUIS: "Defects of phagocyte number, function, or both",
    redFlags: ["aspergillus not treated urgently", "bcg mentioned without contraindication noted", "no antifungal prophylaxis discussed"],
    parentPrompt: `You are the FATHER of Emils, a 3-year-old with recurrent infections. You are frustrated and worried. Answer only what is asked.

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

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.`,
    labData: {
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
    examFindings: "Emils is small — weight 3rd centile, height 10th centile. Poor-quality wound healing visible on legs. Bilateral lymphadenopathy (2–3 cm, firm). Mild hepatosplenomegaly. Perianal fistulous scar. Surgical scar on abdomen from liver drainage. Normal tonsils and oropharynx.",
    modelDiagnosis: "X-linked Chronic Granulomatous Disease (CGD)",
    modelManagement: "Prophylactic TMP-SMX (lifelong, antibacterial). Prophylactic itraconazole/voriconazole (lifelong, antifungal). Treat active Aspergillus with voriconazole IV. IFN-γ therapy (SC 3×/week). Refer for allogeneic HSCT evaluation (curative). BCG permanently contraindicated.",
    modelGeneticCounselling: "X-linked recessive — CYBB on Xp21. Mother is obligate carrier (bimodal DHR confirmed). 25% risk per pregnancy of affected son. Maternal aunt testing recommended. PGT/prenatal diagnosis available. BCG must never be given to males in this family before CGD is excluded.",
    keyClues: ["Normal neutrophil COUNT but recurrent serious infections = qualitative defect", "Serratia marcescens virtually pathognomonic for CGD", "Aspergillus is the most dangerous CGD pathogen", "BCG withheld — family knew risk", "Absent oxidative burst on DHR test", "Maternal nephew with same condition"],
    wrongPaths: {
      "lad": "LAD (Leukocyte Adhesion Deficiency) causes poor wound healing too, but LAD typically shows extreme leukocytosis (WBC >30,000) even when not infected, and does not cause Aspergillus infections. What does the neutrophil COUNT show here?",
      "hies": "HIES (Hyper-IgE Syndrome) also causes S. aureus abscesses, but HIES does not cause liver abscesses, Aspergillus, or Serratia. Also: no eczema, normal IgE. What is the single most important functional test for neutrophils?",
      "cvid": "CVID causes antibody deficiency — but here IgG is ELEVATED (from chronic infection), not low. This pattern suggests a phagocyte defect. What does the lymphocyte subset profile tell you?",
    }
  },
  {
    id: "pfapa", title: "A Girl With Predictable Monthly Fevers", topic: "Autoinflammatory",
    patient: "3-year-old girl", difficulty: "Intermediate",
    openingClinical: "A 3-year-old girl is referred to the Immunology/Rheumatology outpatient clinic with a 14-month history of recurrent febrile episodes. Her mother has kept a fever diary documenting 16 episodes over this period. Each episode lasts 4–6 days and recurs every 3–5 weeks with striking regularity. Between episodes the child is reported to be entirely well. Both parents are from Azerbaijan and are distant relatives (third cousins). MEFV gene sequencing was ordered previously due to ethnic background and has returned negative for pathogenic variants. Her mother is present with the fever diary.",
    opening: "You are seeing a 3-year-old girl and her mother. The mother says: \"She has been getting high fevers since she was one year old. Every 4 or 5 weeks, like clockwork. During the fever she gets a sore throat and swollen neck glands. Then after 4 or 5 days it is completely gone. We are from Azerbaijan — my husband and I are distant relatives, third cousins. The doctors tested her for Mediterranean fever because of our background. The result came back completely negative.\"",
    targetDiagnosis: "PFAPA Syndrome",
    targetIUIS: "Autoinflammatory disorder (not an immunodeficiency)",
    redFlags: ["fever attributed to infection without workup", "colchicine started without clinical indication"],
    parentPrompt: `You are the MOTHER of a 3-year-old girl with recurrent fevers. You and your husband are from Azerbaijan and are distant relatives (third cousins). Answer only what is asked.

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

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.`,
    labData: {
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
    examFindings: "Temperature 40.1°C. Bilateral tender cervical lymph nodes, largest 2 cm. Erythematous pharynx — NO exudate, no pus. Two small aphthous ulcers on inner lower lip. No rash, no arthritis, no hepatosplenomegaly, no abdominal tenderness. Child is alert, not toxic-looking.",
    modelDiagnosis: "PFAPA Syndrome (Periodic Fever, Aphthous stomatitis, Pharyngitis, Adenitis)",
    modelManagement: "Episodic prednisolone 1 mg/kg at fever onset — aborts episode in hours. Warn: steroids shorten inter-episode interval. Consider tonsillectomy (curative ~85–90%) if episodes ≥monthly. Anakinra (anti-IL-1) for refractory cases. MEFV negative — no indication for colchicine.",
    modelGeneticCounselling: "PFAPA has no single causative gene — polygenic/multifactorial. MEFV sequencing is negative for pathogenic variants. Family should understand: this is NOT FMF. Azerbaijani background appropriately triggered testing, but the negative result combined with non-FMF clinical features excludes FMF. Excellent prognosis — spontaneous resolution expected before adolescence.",
    keyClues: ["Perfect periodicity every 4–5 weeks", "Complete wellness between episodes", "Pharyngitis + aphthous ulcers + cervical adenitis = classic PFAPA triad", "No serositis — rules out FMF", "MEFV sequencing negative", "Rapid steroid response (hours) is near-diagnostic", "Maternal history of same condition resolving at age 8"],
    wrongPaths: {
      "fmf": "FMF is a valid concern given the Azerbaijani background — ordering MEFV testing was correct clinical reasoning. However, MEFV sequencing is completely negative for pathogenic variants. Also: FMF episodes last 1–3 days (not 4–6), and FMF requires serositis — abdominal pain, pleuritis. Neither is present here. What does this tell you?",
      "traps": "TRAPS causes periodic fevers too, but TRAPS episodes typically last over 7 days or even weeks, with periorbital oedema and migratory myalgia — all absent here. TNFRSF1A gene is also normal.",
      "bacterial tonsillitis": "Recurrent bacterial tonsillitis is possible, but: all infectious PCRs are negative, procalcitonin is normal, the pattern is perfectly regular (not random), and the fever resolves on day 4–5 regardless of antibiotics. What does the steroid response tell you?",
    }
  },
  {
    id: "hies", title: "A Teenager Whose Eczema Never Responds to Treatment", topic: "Combined Immunodeficiency",
    patient: "13-year-old girl", difficulty: "Advanced",
    openingClinical: "A 13-year-old girl is referred to the Immunology Department by her dermatologist. She has had chronic eczematous skin disease since infancy, attributed to atopic dermatitis in the context of her mother's asthma and hay fever. However, over the past 5 years she has had 3 episodes of pneumonia requiring hospitalisation, the most recent of which demonstrated a cavitary lesion on chest CT. She has also had 4–5 episodes of large skin abscesses draining Staphylococcus aureus, and persistent oral and nail candidiasis recurring shortly after each antifungal course. Her mother is present.",
    opening: "You are seeing a 13-year-old girl and her mother in the immunology clinic. The mother says: \"She has had eczema since she was a baby. The dermatologist has tried everything. It never really goes away. And she keeps getting these big lumps under her arm and on her neck that have to be drained. The surgeons said it is always Staphylococcus. I thought it was connected to my asthma and allergies, but nobody can explain why it keeps happening.\"",
    targetDiagnosis: "Hyper-IgE Syndrome (STAT3 Loss-of-Function)",
    targetIUIS: "Combined immunodeficiency with associated/syndromic features",
    redFlags: ["cold abscesses in child dismissed as atopy", "pneumatocele not monitored", "no antifungal prophylaxis"],
    parentPrompt: `You are the MOTHER of a 13-year-old girl with eczema and recurrent infections. You are worried but somewhat resigned to it being 'just allergy'. Answer only what is asked.

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

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.`,
    labData: {
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
    examFindings: "Lichenified eczema on face, neck, antecubital and popliteal fossae. Dystrophic nails. White candidal plaques on buccal mucosa. 4 retained deciduous teeth (13 years old). Healed scar from abscess drainage on neck. Mild thoracic scoliosis. Normal tonsils. No hepatosplenomegaly.",
    modelDiagnosis: "Hyper-IgE Syndrome (Job Syndrome) — STAT3 loss-of-function, autosomal dominant, de novo",
    modelManagement: "Prophylactic fluconazole (Candida, lifelong). Prophylactic TMP-SMX/cloxacillin (S. aureus). Annual chest CT (pneumatocele monitoring, Aspergillus risk). DEXA scan. Dental panoramic X-ray yearly (retained teeth). Echocardiogram every 2–3 years (coronary artery risk). Live vaccines NOT contraindicated.",
    modelGeneticCounselling: "De novo STAT3 LOF mutation — not inherited from either parent (both negative). Autosomal dominant. Risk to her own future children: 50%. Distinguish from STAT3 GOF (completely different syndrome). Genetic counselling and reproductive options available.",
    keyClues: ["Cold abscesses — large, painless, non-inflammatory", "IgE >2,000 exceeds atopic range", "Retained primary teeth at age 13 (pathognomonic skeletal feature)", "Scoliosis (another skeletal feature)", "Absent Th17 cells and undetectable IL-17A", "Pneumatocele on chest CT", "De novo STAT3 LOF mutation"],
    wrongPaths: {
      "atopy": "Severe atopy is a reasonable first thought given the family history and high IgE. However: atopic dermatitis does NOT cause cold abscesses (large, painless, non-inflammatory purulent lesions). It does NOT cause retained primary teeth or scoliosis. And IgE >2,000 is extreme even for very severe atopy. Which findings cannot be explained by atopy alone?",
      "cmc": "Chronic mucocutaneous candidiasis could explain the recurrent candidiasis — and absent Th17 cells are present in both CMC and HIES. However, CMC does not explain the cold S. aureus abscesses, pneumatocele, or skeletal features. The full syndrome points toward a broader STAT3 defect.",
      "cgd": "CGD causes deep S. aureus abscesses, but CGD abscesses are typically HOT and inflammatory, not cold. Also: no Serratia, no Aspergillus, no liver abscess; normal oxidative burst expected in HIES. What is the key functional T-cell defect here?",
    }
  },
  {
    id: "scid", title: "A Baby With Infections After BCG Vaccination", topic: "SCID / Combined Immunodeficiency",
    patient: "Male infant, 2.5 months old", difficulty: "Advanced",
    openingClinical: "A 2.5-month-old male infant is admitted to the Immunology Department from a regional hospital. He presented with erythroderma, a widespread maculopapular rash covering the trunk and extremities, and pneumonia with acute bronchiolitis. His mother reports that he appeared healthy at birth and was discharged on day 3 of life. BCG vaccination was delayed to 2 months of age due to parental hesitancy. The rash appeared shortly after BCG vaccination. He subsequently developed pneumonia and a bacterial skin infection. He has been hospitalised continuously since age 2.5 months. This is the family's first child; parents are non-consanguineous with no known family history of immunodeficiency.",
    opening: "You are seeing a 2.5-month-old male infant and his mother in hospital. The baby was admitted with erythroderma, a maculopapular rash all over his body, and pneumonia. His mother says: \"He seemed healthy when he was born. We delayed the tuberculosis vaccine until he was two months old because we had some worries. Shortly after he got it, he developed this rash all over his body. Then he started getting chest infections. He has been in hospital ever since. The doctors say his immune system may not be working.\"",
    targetDiagnosis: "SCID — Artemis deficiency (DCLRE1C), T⁻B⁻NK⁺, complicated by maternal T-cell engraftment",
    targetIUIS: "Combined T and B cell immunodeficiency",
    redFlags: ["live vaccines not immediately contraindicated", "no urgent HSCT referral", "bcg disease not treated", "no isolation precautions mentioned"],
    parentPrompt: `You are the MOTHER of a 2.5-month-old male infant who has been very sick since shortly after BCG vaccination. You are frightened. Answer only what is asked.

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

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.`,
    labData: {
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
    examFindings: "Widespread erythroderma and maculopapular rash. Oral candidiasis. Accessory muscle use and wheeze consistent with bronchiolitis. NO palpable lymph nodes. Tonsils present. BCG injection site: 10mm cyanotic induration. Left axillary lymphadenopathy. No hepatosplenomegaly at this time.",
    modelDiagnosis: "Artemis-deficient SCID (DCLRE1C null variant) — T⁻B⁻NK⁺ phenotype with maternal T-cell engraftment and disseminated BCGitis",
    modelManagement: "IMMEDIATE: (1) Protective isolation. (2) All live vaccines permanently contraindicated. (3) Start antimycobacterial therapy (ethambutol + levofloxacin + rifampicin). (4) IVIG for hypogammaglobulinaemia. (5) TMP-SMX prophylaxis (Pneumocystis). URGENT HSCT referral — SCID is universally fatal without transplant. Monitor for rifampicin–cyclosporine A drug interaction post-HSCT.",
    modelGeneticCounselling: "Autosomal recessive — DCLRE1C. Both parents are obligate carriers. 25% recurrence risk per pregnancy. Prenatal diagnosis/PGT available. Radiosensitivity — minimise ionising radiation lifelong. BCG must not be given to any future sibling before SCID is excluded. TREC newborn screening now available in Latvia (since April 1, 2023).",
    keyClues: ["BCG vaccination → erythroderma = SCID alarm signal", "Critically low ABSOLUTE lymphocyte count (not just percentage)", "Virtually absent CD8+ cells", "Severely absent B cells", "Maternal T-cell engraftment masking the diagnosis (CD3% appears normal)", "Disseminated BCGitis confirmed by stool MTB PCR", "DCLRE1C null variant — Artemis deficiency"],
    wrongPaths: {
      "omenn": "Omenn syndrome is an important differential — both cause erythroderma, eosinophilia, and circulating T cells. Key distinction: Omenn T cells are AUTOLOGOUS (patient's own autoreactive cells from hypomorphic mutations) and typically show markedly elevated IgE. Here, T cells are MATERNAL (allogeneic), IgE is very low, and chimerism studies confirm maternal origin. How would you distinguish these?",
      "atopy": "Atopic dermatitis cannot explain IgG 0.32 g/L, virtually absent B cells, absent CD8+ cells, or a critically low absolute lymphocyte count. The combination of severe rash + after BCG + profoundly low lymphocytes points to a life-threatening immunodeficiency.",
      "cvid": "CVID typically presents in the 2nd–3rd decade, not at 2.5 months. Also: the absolute lymphocyte count is critically low and CD8+ cells are virtually absent — CVID does not cause this pattern in infancy.",
    }
  },
  {
    id: "thi", title: "A Baby Referred for Low IgG", topic: "Antibody Deficiency (Transient)",
    patient: "10-month-old boy (Toms)", difficulty: "Beginner",
    openingClinical: "A 10-month-old boy, Toms, is referred to the Immunology Department outpatient clinic following an incidental finding of low serum IgG on a blood test ordered by his paediatrician. He has had three episodes of acute otitis media in the past four months and one episode of bronchitis, all treated successfully with standard oral antibiotics. His growth is following the 25th centile. There is no history of severe infections, hospitalisation, skin abscesses, fungal infections, or failure to thrive. His father had frequent ear infections throughout infancy, described by his own family doctor as 'low antibodies that resolved by age 3–4.' His mother is present and anxious.",
    opening: "You are seeing Toms, a 10-month-old boy, and his mother. She says: \"Our paediatrician sent us here because his IgG came back low on a blood test. He has had three ear infections in four months and one chest infection. She called us very worried and said he might have an immune problem. We are very anxious.\"",
    targetDiagnosis: "Transient Hypogammaglobulinaemia of Infancy (THI)",
    targetIUIS: "Predominantly antibody deficiency — unclassified/transient",
    redFlags: ["ivig started for mild thi without indication", "xla not properly excluded"],
    parentPrompt: `You are the MOTHER of Toms, a 10-month-old boy referred for low IgG. You are anxious but the child is essentially well. Answer only what is asked.

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

Keep answers 2–4 sentences. Natural language. Do NOT reveal the diagnosis.`,
    labData: {
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
    examFindings: "Weight 8.9 kg (25th centile — tracking appropriately). Tonsils PRESENT and normal. Bilateral tympanic membrane dullness (otitis media with effusion). Small bilateral cervical nodes (0.5–1 cm, normal). No hepatosplenomegaly. No rash. No candidiasis. No absent lymphoid tissue.",
    modelDiagnosis: "Transient Hypogammaglobulinaemia of Infancy (THI)",
    modelManagement: "Watchful waiting (no IVIG today — mild infections, growth maintained, B cells present). Prophylactic amoxicillin for recurrent otitis media. Repeat serum Ig every 3–4 months. Check vaccine antibody titres post-booster at 12 months. IVIG only if: ≥2 serious bacterial infections/year, invasive infection, or failure to thrive. If IgG still low at age 4 with absent vaccine responses → redefine as CVID.",
    modelGeneticCounselling: "THI has no single causative gene — polygenic/multifactorial. Father's history of 'low antibodies as an infant, resolved at age 3–4' is consistent with familial THI tendency. No X-linked risk: mother is not a BTK carrier. Future siblings: modestly elevated background risk of THI but no Mendelian recurrence risk. Key message: This is not the serious immunodeficiency that was feared. Toms almost certainly has the same benign pattern his father had.",
    keyClues: ["Onset after 6 months (after maternal IgG wanes — same as XLA, but different mechanism)", "Infections mild — responding to standard antibiotics", "Tonsils PRESENT (unlike XLA)", "B cells PRESENT and normal on flow cytometry (excludes all agammaglobulinaemia)", "BTK normal (excludes XLA)", "Father had identical history resolving at age 3–4", "IgM preserved (T-independent responses maintained)"],
    wrongPaths: {
      "xla": "XLA is the critical diagnosis to exclude here — both present with low IgG in a male infant after 6 months. The key distinction: B cells. In XLA, CD19+ B cells are completely ABSENT (0%). Here, B cells are PRESENT and NORMAL at 12%. BTK protein is also normal. XLA cannot coexist with normal B cells. What does this tell you about the diagnosis?",
      "start ivig immediately": "IVIG in mild THI is not evidence-based and may cause harm — it suppresses endogenous IgG production by feedback inhibition, potentially delaying natural resolution. Is there evidence of serious bacterial infections, invasive infection, or failure to thrive here? Infections are mild, growth is maintained, and B cells are present and maturing. What is the appropriate management for this severity?",
      "cvid": "CVID is a valid concern if low IgG persists — but at 10 months, it is far too early to diagnose CVID, which typically presents in the 2nd–3rd decade. CVID also requires persistent deficiency beyond age 4 with absent vaccine responses. What should the monitoring plan be?",
    }
  }
];

// ── API ───────────────────────────────────────────────────────────────────────
async function callClaude(messages, system, maxTokens = 400) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-allow-browser": "true",
    },
    body: JSON.stringify({ model: "claude-sonnet-4-6", max_tokens: maxTokens, system, messages }),
  });
  const d = await r.json();
  if (d.error) throw new Error(d.error.message);
  return d.content[0].text;
}

// ── LAB TEXT → TABLE ROWS ─────────────────────────────────────────────────────
// Parses a free-text result string into structured rows for table rendering.
// Each sentence becomes a row; colon-separated lines get param | value columns.
function parseLabText(text) {
  // Split on sentence boundaries while preserving content
  const raw = text
    .replace(/\. NOTE:/gi, "\nNOTE:")
    .replace(/\. ⚠/g, "\n⚠")
    .replace(/\. KEY:/gi, "\nKEY:")
    .split(/\.\s+(?=[A-Z])/)
    .map(s => s.trim().replace(/\.$/, "").trim())
    .filter(Boolean);

  return raw.map(sentence => {
    // Note / warning lines
    if (/^(NOTE|⚠|KEY|IMPORTANT|WARNING)[:!]/i.test(sentence)) {
      return { type: "note", text: sentence.replace(/^(NOTE|⚠|KEY|IMPORTANT|WARNING)[:!]\s*/i, "") };
    }
    // Colon-separated: "Parameter: Value"
    const colonIdx = sentence.indexOf(":");
    if (colonIdx > 0 && colonIdx < 60) {
      return {
        type: "row",
        param: sentence.substring(0, colonIdx).trim(),
        value: sentence.substring(colonIdx + 1).trim(),
      };
    }
    // "WORD(S) numeric/value" — e.g. "WBC 6,200/µL (normal)"
    const m = sentence.match(/^([A-Za-z][A-Za-z0-9+\-\/\s]{0,35}?)\s+([<>≤≥~]?[\d\.,]+.*)$/);
    if (m) {
      return { type: "row", param: m[1].trim(), value: m[2].trim() };
    }
    // Full-width note row
    return { type: "note", text: sentence };
  });
}

function flagRow(value) {
  const v = value.toUpperCase();
  if (/↑↑↑|CRITICALLY/.test(v))    return "crit";
  if (/↑↑|MARKEDLY ELEVATED/.test(v)) return "hi2";
  if (/↑|ELEVATED|HIGH|POSITIVE(?! FOR)|RAISED/.test(v)) return "hi";
  if (/ABSENT|UNDETECTABLE|0\.0%|VIRTUALLY ABSENT/.test(v)) return "absent";
  if (/DIAGNOSTIC|PATHOGNOMONIC/.test(v)) return "diag";
  if (/↓↓↓|SEVERELY (LOW|DECREASED)|CRITICALLY LOW/.test(v)) return "lo3";
  if (/↓↓|MARKEDLY (LOW|DECREASED)/.test(v)) return "lo2";
  if (/↓|LOW|DECREASED|BELOW REFERENCE/.test(v)) return "lo";
  if (/NORMAL|NEGATIVE|NO GROWTH|NO PATHOGEN|NO SIGNIFICANT|INTACT|PRESENT AND NORMAL/.test(v)) return "ok";
  return "neutral";
}

const FLAG_STYLE = {
  crit:    { bg:"#FFF0F0", text:"#8B0000", badge:"CRITICAL",   badgeBg:"#C03030", badgeText:"#fff" },
  hi2:     { bg:"#FFF4EC", text:"#8B3A00", badge:"↑↑",         badgeBg:"#C05020", badgeText:"#fff" },
  hi:      { bg:"#FFFBF0", text:"#7B4A00", badge:"↑",          badgeBg:"#B07020", badgeText:"#fff" },
  absent:  { bg:"#F5F0FF", text:"#4A1A7A", badge:"ABSENT",     badgeBg:"#7040B0", badgeText:"#fff" },
  diag:    { bg:"#F0FFF4", text:"#1A5E30", badge:"DIAGNOSTIC",  badgeBg:"#1D7A40", badgeText:"#fff" },
  lo3:     { bg:"#EEF4FF", text:"#1A3A8B", badge:"↓↓↓",        badgeBg:"#2050B0", badgeText:"#fff" },
  lo2:     { bg:"#F0F5FF", text:"#1A408B", badge:"↓↓",         badgeBg:"#2060B0", badgeText:"#fff" },
  lo:      { bg:"#F2F6FF", text:"#204890", badge:"↓",          badgeBg:"#3070C0", badgeText:"#fff" },
  ok:      { bg:"#F5FFF8", text:"#1A5030", badge:null,         badgeBg:null,      badgeText:null  },
  neutral: { bg:"transparent", text:"#1A1714", badge:null,     badgeBg:null,      badgeText:null  },
};

function formatLabResult(testName, resultText) {
  return `__LAB__${testName}\n${resultText}`;
}

// ── TEST ALIAS MAP ────────────────────────────────────────────────────────────
// Maps every way a student might name a test → canonical labData key fragment
const TEST_ALIASES = [
  // CBC
  { aliases: ["cbc","full blood count","fbc","complete blood count","blood count","haemoglobin","hemoglobin","hb","wbc","white cell","white blood","neutrophil count","eosinophil","platelet","lymphocyte count","differential","alc","absolute lymphocyte"], key: "CBC" },
  // CRP
  { aliases: ["crp","c reactive","c-reactive","inflammatory marker"], key: "CRP" },
  // ESR
  { aliases: ["esr","erythrocyte sedimentation"], key: "ESR" },
  // Procalcitonin
  { aliases: ["procalcitonin","pct"], key: "procalcitonin" },
  // Blood biochemistry (combined LFT + U&E + metabolic)
  { aliases: ["biochemistry","blood biochemistry","lft","liver function","renal function","urea","creatinine","electrolytes","electrolyte","u&e","u and e","kidney function","egfr","sodium","potassium","glucose","alt","ast","bilirubin","albumin","total protein","metabolic panel","liver enzyme","liver panel","hepatic"], key: "blood biochemistry" },
  // Immunoglobulins
  { aliases: ["immunoglobulin","igg","iga","igm","ige","igd","antibody level","serum protein","protein electrophoresis","spep"], key: "immunoglobulin" },
  // Complement
  { aliases: ["complement","c3","c4","ch50","ch 50"], key: "complement" },
  // Blood culture
  { aliases: ["blood culture","bacteraemia","bacteremia","sepsis screen","bcx"], key: "blood culture" },
  // Urinalysis
  { aliases: ["urinalysis","urine","urine dip","dipstick","urine mc&s","urine culture","mid stream","mcsu","mssu","urine dipstick"], key: "urinalysis" },
  // Throat swab
  { aliases: ["throat swab","throat culture","throat pcr","throat","rapid strep","strep test","rapid antigen"], key: "throat" },
  // Ear swab
  { aliases: ["ear swab","ear culture","ear discharge","aural swab"], key: "ear swab" },
  // Skin / wound swab
  { aliases: ["skin swab","wound swab","wound culture","abscess culture","abscess swab","skin culture","lesion swab","pus swab","pus culture"], key: "wound swab" },
  // Stool
  { aliases: ["stool","faeces","feces","stool culture","stool pcr","mtb pcr","tuberculosis pcr","bcg pcr","gastric lavage","giardia","stool examination","ova cyst"], key: "stool" },
  // Sputum / BAL
  { aliases: ["sputum","bal","bronchoalveolar","bronchoscopy","sputum culture","galactomannan","aspergillus pcr"], key: "sputum" },
  // Chest X-ray
  { aliases: ["chest xray","chest x-ray","chest x ray","cxr","cxr chest","chest film","chest radiograph","x ray chest","xray chest","plain film","plain chest","erect chest"], key: "chest X-ray" },
  // Chest CT
  { aliases: ["chest ct","ct chest","ct thorax","hrct","high resolution ct","lung ct","ct scan chest","ct pulmonary"], key: "chest CT" },
  // Abdominal imaging
  { aliases: ["abdominal ultrasound","abdominal us","abdominal scan","abdo us","abdo scan","liver scan","abdominal ct","ct abdomen","liver ultrasound","renal ultrasound","usg abdomen","abdominal imaging"], key: "abdominal" },
  // Spine / skeletal
  { aliases: ["spine xray","spine x-ray","scoliosis xray","skeletal xray","bone xray","bone scan","dexa","bone density","spinal xray"], key: "spine" },
  // Dental / OPG
  { aliases: ["dental xray","opg","orthopantomogram","dental panoramic","panoramic xray"], key: "dental" },
  // Echocardiogram
  { aliases: ["echo","echocardiogram","cardiac echo","heart scan","cardiac ultrasound","ecg","ekg","electrocardiogram"], key: "echocardiogram" },
  // Lymphocyte subsets / flow
  { aliases: ["lymphocyte subset","flow cytometry","flow cytometry","lymphocyte panel","t cell","b cell","nk cell","cd3","cd4","cd8","cd19","cd16","cd56","btk protein","btk expression","immunophenotyping","facs"], key: "lymphocyte subsets" },
  // Vaccine antibodies
  { aliases: ["vaccine antibody","vaccine titre","vaccine titer","pneumococcal antibody","tetanus antibody","hib antibody","specific antibody","functional antibody","protective antibody"], key: "vaccine antibody" },
  // HIV
  { aliases: ["hiv","retrovirus","hiv test","hiv serology"], key: "HIV" },
  // DHR / oxidative burst
  { aliases: ["dhr","dihydrorhodamine","oxidative burst","neutrophil function","phagocyte function","nbt","nitroblue","oxidative killing"], key: "DHR" },
  // TREC
  { aliases: ["trec","t cell receptor excision","newborn screening","trec assay"], key: "TREC" },
  // Chimerism
  { aliases: ["chimerism","qf-pcr","maternal engraftment","maternal t cell","qfpcr","chimerism testing"], key: "chimerism" },
  // Gene panel / genetic
  { aliases: ["gene panel","genetic panel","genetic testing","exome","wes","whole exome","ngs","next generation","immunodeficiency panel","iei panel","primary immunodeficiency panel","gene sequencing","genetic sequencing"], key: "immunodeficiency gene panel" },
  // Autoinflammatory / MEFV
  { aliases: ["autoinflammatory","mefv","fmf gene","mediterranean fever gene","traps gene","tnfrsf1a","mvk","hids","nlrp3","caps","autoinflammatory panel"], key: "autoinflammatory" },
  // Cytokines
  { aliases: ["cytokine","il-17","il17","interleukin","il-1","il1","interferon","tnf","cytokine panel"], key: "cytokine" },
  // Monospot / EBV
  { aliases: ["monospot","ebv serology","ebv antibody","glandular fever","infectious mono","mono test"], key: "monospot" },
  // Ferritin
  { aliases: ["ferritin","iron studies","iron level","transferrin","tsat"], key: "ferritin" },
  // Skin biopsy
  { aliases: ["skin biopsy","biopsy","punch biopsy","histology","histopathology"], key: "skin biopsy" },
  // Lateral neck X-ray
  { aliases: ["lateral neck","adenoid xray","adenoid xray","neck xray","lateral neck xray"], key: "lateral neck" },
  // Colonoscopy
  { aliases: ["colonoscopy","colonic biopsy","bowel biopsy","gi endoscopy","endoscopy","colonoscope"], key: "colonoscopy" },
  // NIH HIES score
  { aliases: ["hies score","nih score","nih hies","job score"], key: "NIH HIES" },
];

// Extract test names from free text
function detectTestsInMessage(text) {
  const lower = text.toLowerCase();
  const found = [];
  for (const entry of TEST_ALIASES) {
    if (entry.aliases.some(alias => lower.includes(alias))) {
      found.push(entry.key);
    }
  }
  return [...new Set(found)];
}

// Is this message ordering a test?
function isTestOrder(text) {
  const lower = text.toLowerCase();
  const orderWords = ["order","request","would like","i'd like","i want","can we","let's","let us","please send","please get","please check","send off","check a","get a","run a","do a","do some","take a","arrange","perform","carry out","i need","we need","please do","can you get","can you check","can you order","can you run","could we","could you get"];
  const hasOrderWord = orderWords.some(w => lower.includes(w));
  const tests = detectTestsInMessage(text);
  // Either: explicit order word + test name, OR just test name abbreviations typed alone
  const isJustTestNames = /^[\w\s,/+&\-\.()]+$/.test(text) && text.length < 80 && tests.length > 0;
  return (hasOrderWord && tests.length > 0) || isJustTestNames;
}

// Find labData result for a matched key fragment
function findLabResult(caseLabData, keyFragment) {
  const lower = keyFragment.toLowerCase();
  const entry = Object.entries(caseLabData).find(([k]) =>
    k.toLowerCase().includes(lower) || lower.split(" ").some(w => w.length > 2 && k.toLowerCase().includes(w))
  );
  return entry || null;
}
const makeTutorPrompt = (c, phase, mode) => `You are the CLINICAL TUTOR in a medical student training simulation for Inborn Errors of Immunity.

Current case: "${c.title}" — Target diagnosis: ${c.targetDiagnosis}
Current phase: ${phase}
Mode: ${mode}

TUTOR RULES:
- Be supportive, educational, and non-punitive. Never say "Wrong."
- Use phrases like: "One finding does not fully fit..." / "Compare X and Y..." / "What finding supports...?"
- Give formative guidance, not the answer directly
- In EXAM mode: be more concise, less proactive with hints

MISTAKE HANDLING LEVELS:
L1 (minor): Gentle redirect — "One finding doesn't fully fit. Which result would you reconsider?"
L2 (close but wrong): Guided comparison — "Compare [wrong diagnosis] and [correct one]. Which better explains [key finding]?"
L3 (unsupported): Ask for justification — "What specific findings support this?"
L4 (safety issue): Alert — "Safety alert: In a child with [condition], [action] is important. What immediate steps are needed?"
L5 (stuck): Offer hints in levels if practice mode

WRONG PATH GUIDANCE (use these specific redirects):
${Object.entries(c.wrongPaths).map(([k,v]) => `- If student says "${k}": ${v}`).join("\n")}

KEY CLUES they should find: ${c.keyClues.join("; ")}`;

const makeFeedbackPrompt = (c) => `You are generating STRUCTURED FORMATIVE FEEDBACK for a clinical immunology case simulation.

Case: "${c.title}"
Target diagnosis: ${c.targetDiagnosis}
IUIS category: ${c.targetIUIS}
Key clues: ${c.keyClues.join("; ")}
Model management: ${c.modelManagement}
Model genetic counselling: ${c.modelGeneticCounselling}

Generate feedback in this EXACT JSON structure (no markdown, pure JSON):
{
  "diagnosticAccuracy": "correct|partially_correct|incorrect",
  "diagnosticComment": "1-2 sentences on diagnosis accuracy",
  "wellDone": ["point1", "point2", "point3"],
  "missing": ["point1", "point2"],
  "keyClues": ["clue1", "clue2", "clue3"],
  "reasoningPathway": "3-4 sentence ideal reasoning pathway",
  "managementPoints": ["point1", "point2", "point3"],
  "geneticPoints": ["point1", "point2"],
  "revisionTopic": "1-2 sentence suggested revision topic",
  "scores": {
    "historyTaking": "Excellent|Good|Developing|Needs review",
    "examination": "Excellent|Good|Developing|Needs review",
    "differential": "Excellent|Good|Developing|Needs review",
    "testSelection": "Excellent|Good|Developing|Needs review",
    "interpretation": "Excellent|Good|Developing|Needs review",
    "management": "Excellent|Good|Developing|Needs review"
  }
}`;

// ── COLOURS ────────────────────────────────────────────────────────────────────
const C = {
  bg: "#F8F6F0", surface: "#FFFFFF", surfaceAlt: "#F2EFE8",
  border: "#DDD8CC", borderDark: "#BEB9AD",
  navy: "#1A2B4A", navyLight: "#2D4670", navyPale: "#EDF0F7",
  teal: "#2A6B5C", tealLight: "#3D8A76", tealPale: "#E8F4F1",
  amber: "#8B5E00", amberPale: "#FFF8E6",
  red: "#8B1A1A", redPale: "#FDF0F0",
  muted: "#6B6560", dim: "#9C978E",
  text: "#1A1714", textLight: "#3D3935",
  parent: "#2A4A2A", parentBg: "#EFF7EF", parentBorder: "#B8D8B8",
  tutor: "#1A2B5A", tutorBg: "#EEF2FB", tutorBorder: "#B0C0E0",
  safety: "#6B1A1A", safetyBg: "#FDF0F0", safetyBorder: "#E0B0B0",
  student: "#FFFFFF", studentBg: "#1A2B4A", studentBorder: "#1A2B4A",
  lab: "#2A3A2A", labBg: "#F4FAF4", labBorder: "#90C090",
  labHi: "#7A1A00", labLo: "#003A7A", labTag: "#1E5C1E",
};

const PHASE_LABELS = {
  history: "History Taking",
  summary: "Clinical Summary",
  examination: "Physical Examination",
  differential: "Differential Diagnosis",
  tests: "Investigations",
  interpretation: "Interpretation",
  final: "Final Answer",
  feedback: "Feedback Report",
  reflection: "Reflection",
};

const PHASE_ORDER = ["history","summary","examination","differential","tests","interpretation","final","feedback"];

export default function App() {
  const [screen, setScreen] = useState("welcome"); // welcome | mode | case | chat | feedback
  const [mode, setMode] = useState("practice");
  const [selCase, setSelCase] = useState(null);
  const [phase, setPhase] = useState("opening");
  const [msgs, setMsgs] = useState([]); // { role, text, type: 'parent'|'tutor'|'student'|'system'|'safety' }
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [orderedTests, setOrderedTests] = useState(new Set());
  const [examDone, setExamDone] = useState(false);
  const [summary, setSummary] = useState("");
  const [differentials, setDifferentials] = useState("");
  const [finalAnswer, setFinalAnswer] = useState({ diagnosis: "", findings: "", differentials: "", tests: "", management: "", genetics: "", explanation: "" });
  const [feedback, setFeedback] = useState(null);
  const [reflectionStep, setReflectionStep] = useState(0);
  const [reflectionAnswers, setReflectionAnswers] = useState([]);
  const [inputMode, setInputMode] = useState("history"); // history | test_order | summary_input | diff_input | interp_input | final_form
  const [showHintMenu, setShowHintMenu] = useState(false);
  const [hintPopup, setHintPopup] = useState(null);
  const [interpText, setInterpText] = useState("");
  const [interpResult, setInterpResult] = useState("");
  const [showFinalForm, setShowFinalForm] = useState(false);
  const [showTestPanel, setShowTestPanel] = useState(false);
  const [activeTab, setActiveTab] = useState("consultation"); // consultation | investigations | diagnosis
  const chatEnd = useRef(null);
  const labEnd = useRef(null);

  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, busy]);

  const addMsg = (text, type) => setMsgs(m => [...m, { text, type, id: Date.now() + Math.random() }]);

  const [seenCases, setSeenCases] = useState(() => {
    // Read immediately on mount — localStorage is synchronous, no loading state needed
    try {
      const stored = localStorage.getItem("iei_seen_cases");
      return stored ? JSON.parse(stored) : [];
    } catch { return []; }
  });
  const [storageLoaded] = useState(true); // always true — localStorage is synchronous
  const [showBrowse, setShowBrowse] = useState(false);
  const [allDone, setAllDone] = useState(false);

  const saveSeenCase = (caseId, currentSeen) => {
    const updated = [...new Set([...currentSeen, caseId])];
    setSeenCases(updated);
    try { localStorage.setItem("iei_seen_cases", JSON.stringify(updated)); } catch {}
  };

  const resetProgress = () => {
    setSeenCases([]);
    setAllDone(false);
    try { localStorage.removeItem("iei_seen_cases"); } catch {}
  };

  const startRandomCase = () => {
    const unseen = CASES.filter(c => !seenCases.includes(c.id));
    if (unseen.length === 0) { setAllDone(true); return; }
    const pick = unseen[Math.floor(Math.random() * unseen.length)];
    saveSeenCase(pick.id, seenCases);
    startCase(pick);
  };

  const startCase = (c) => {
    setSelCase(c);
    setPhase("history");  // start here so investigations button is visible immediately
    setMsgs([]);
    setInput("");
    setHintsUsed(0);
    setHintPopup(null);
    setOrderedTests(new Set());
    setExamDone(false);
    setSummary("");
    setDifferentials("");
    setFinalAnswer({ diagnosis: "", findings: "", differentials: "", tests: "", management: "", genetics: "", explanation: "" });
    setFeedback(null);
    setInputMode("history");
    setShowFinalForm(false);
    setInterpText("");
    setInterpResult("");
    setReflectionStep(0);
    setReflectionAnswers([]);
    setShowBrowse(false);
    setAllDone(false);
    setShowTestPanel(false);
    setActiveTab("consultation");
    // Use clinical description, not mother's speech
    addMsg(
      `📍 Immunology Department — Outpatient Clinic\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n${c.openingClinical}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nThe parent is present and willing to speak with you. You may begin taking history.\n\n📌 Use the tabs at the top to navigate:\n  • 💬 Consultation — ask the parent questions and receive examination findings\n  • 🔬 Investigations — switch here to order tests and view results\n  • 📋 Final Diagnosis — submit your diagnosis and management plan when ready`,
      "system"
    );
    setScreen("chat");
  };

  const sendMessage = async () => {
    if (!input.trim() || busy) return;
    const userText = input.trim();
    setInput("");
    addMsg(userText, "student");
    setBusy(true);

    // ── SCID worsening trigger ────────────────────────────────────────────────
    if (selCase.id === "scid" && phase === "history" && msgs.length > 8) {
      const hasUrgent = msgs.some(m => m.text.toLowerCase().match(/isolat|live.vacc|urgent|referral|prophylaxis|contact precaution/));
      if (!hasUrgent && Math.random() > 0.6) {
        addMsg("Doctor, I am getting worried — he seems more tired today and has developed a fever again. The rash is spreading. Is it safe for us to go home?", "parent");
        setTimeout(() => addMsg("🟡 Clinical reasoning note: This may be a time-sensitive situation. Some immunodeficiencies require urgent management before the final genetic diagnosis is confirmed. What immediate steps are needed — regarding isolation, vaccination history, and referral?", "tutor"), 800);
        setBusy(false);
        return;
      }
    }

    // ── TEST ORDER DETECTION ──────────────────────────────────────────────────
    if (isTestOrder(userText)) {
      const detectedKeys = detectTestsInMessage(userText);
      const newOrdered = new Set(orderedTests);
      let anyNew = false;

      if (["history","summary","examination","differential"].includes(phase)) {
        setPhase("tests");
      }

      for (const key of detectedKeys) {
        if (newOrdered.has(key)) continue; // already ordered
        anyNew = true;
        newOrdered.add(key);

        const result = findLabResult(selCase.labData, key);
        if (result) {
          const isGenetic = /gene panel|genetic|exome|sequencing/i.test(result[0]);
          addMsg(formatLabResult(result[0], result[1]), "lab");
          if (isGenetic && newOrdered.size < 4 && mode === "practice") {
            setTimeout(() => addMsg("💡 Clinical reasoning note: Genetic testing has been ordered. It is good practice to first characterise the immunological phenotype with basic immune tests before interpreting genetic findings. Are the basic immune results consistent with the genetic result?", "lab_tutor"), 600);
          }
        } else {
          addMsg(`📋 ${key}: Results not yet available.`, "system");
        }
      }

      if (anyNew) {
        addMsg("🔬 Investigations ordered — switch to the Investigations tab to see results.", "system");
      } else {
        addMsg("These investigations have already been ordered.", "system");
      }

      setOrderedTests(newOrdered);
      setBusy(false);
      return;
    }

    // ── NORMAL HISTORY MESSAGE → send to parent AI ─────────────────────────
    try {
      const history = msgs.slice(-12).map(m => ({
        role: m.type === "student" ? "user" : "assistant",
        content: m.type === "lab" ? `[Lab result shown]` : m.text,
      }));
      history.push({ role: "user", content: userText });

      const reply = await callClaude(history, selCase.parentPrompt, 300);
      addMsg(reply, "parent");

      // Proactive tutor nudge after 5 parent responses — suggest physical exam if not yet done
      if (mode === "practice" && phase === "history" && !examDone && msgs.filter(m => m.type === "parent").length === 5) {
        setTimeout(() => addMsg("💡 Clinical reasoning note: You have gathered some initial history. Consider whether a physical examination would add useful information at this point — you can request one at any time.", "tutor"), 600);
      }
    } catch (e) {
      addMsg("⚠ Connection error. Please try again.", "system");
    }
    setBusy(false);
  };

  const requestExam = async () => {
    if (busy) return;
    setBusy(true);
    addMsg("I would like to perform a physical examination.", "student");
    await new Promise(r => setTimeout(r, 400));
    addMsg(`📋 Physical examination findings:\n\n${selCase.examFindings}`, "system");
    setExamDone(true);
    if (mode === "practice") {
      addMsg("💡 Consider what the examination findings add to your differential diagnosis. Are there any pathognomonic signs?", "tutor");
    }
    setBusy(false);
  };

  const orderTest = (testName) => {
    // Direct call pathway — used if panel quick-order kept
    if (orderedTests.has(testName)) return;
    const newOrdered = new Set(orderedTests);
    newOrdered.add(testName);
    setOrderedTests(newOrdered);
    if (["history","summary","examination","differential"].includes(phase)) setPhase("tests");
    addMsg(`📋 Ordered: ${testName}`, "student");
    const result = findLabResult(selCase.labData, testName);
    if (result) addMsg(formatLabResult(result[0], result[1]), "lab");
    else addMsg(`⚠ "${testName}" — no result available in this case panel.`, "system");
  };

  const sendTestOrder = () => {
    if (!input.trim() || busy) return;
    const userText = input.trim();
    setInput("");
    const detectedKeys = detectTestsInMessage(userText);

    if (detectedKeys.length === 0) {
      addMsg(`⚠ "${userText}" was not recognised. Try a name like "CBC", "immunoglobulins", "chest X-ray", or "flow cytometry".`, "lab_note");
      return;
    }

    if (["history","summary","examination","differential"].includes(phase)) setPhase("tests");

    const newOrdered = new Set(orderedTests);
    let anyNew = false;

    for (const key of detectedKeys) {
      if (newOrdered.has(key)) continue;
      anyNew = true;
      newOrdered.add(key);
      const result = findLabResult(selCase.labData, key);
      if (result) {
        const isGenetic = /gene panel|genetic|exome|sequencing/i.test(result[0]);
        addMsg(formatLabResult(result[0], result[1]), "lab");
        if (isGenetic && newOrdered.size < 4 && mode === "practice") {
          setTimeout(() => addMsg("💡 Clinical reasoning note: Genetic testing has been ordered. It is good practice to first characterise the immunological phenotype with basic immune tests before interpreting genetic findings. Are the basic immune results consistent with the genetic result?", "lab_tutor"), 600);
        }
      } else {
        addMsg(`📋 ${key}: Results not yet available for this case.`, "lab_note");
      }
    }

    if (!anyNew) {
      addMsg("These investigations have already been ordered.", "lab_note");
    }

    setOrderedTests(newOrdered);
    setTimeout(() => labEnd.current?.scrollIntoView({ behavior: "smooth" }), 100);
  };

  const submitSummary = async () => {
    if (!summary.trim() || busy) return;
    setBusy(true);
    addMsg(`📝 Clinical summary:\n${summary}`, "student");
    const sys = `${makeTutorPrompt(selCase, "summary", mode)}\n\nEvaluate this clinical summary from a medical student (3–4 sentences, encouraging, identify what's good and what's missing).`;
    const fb = await callClaude([{ role: "user", content: summary }], sys, 300);
    addMsg(`💡 Clinical reasoning note:\n${fb}`, "tutor");
    setPhase("examination");
    setInputMode("history");
    setBusy(false);
  };

  const submitDifferentials = async () => {
    if (!differentials.trim() || busy) return;
    setBusy(true);
    addMsg(`📋 My differential diagnoses:\n${differentials}`, "student");
    const isWrong = Object.keys(selCase.wrongPaths).some(k => differentials.toLowerCase().includes(k));
    let fbText;
    if (isWrong) {
      const wrongKey = Object.keys(selCase.wrongPaths).find(k => differentials.toLowerCase().includes(k));
      fbText = `💡 Clinical reasoning note:\n${selCase.wrongPaths[wrongKey]}`;
    } else {
      const sys = `${makeTutorPrompt(selCase, "differential", mode)}\n\nEvaluate these differentials from a medical student. Be encouraging, guide without giving away the answer. 3–5 sentences.`;
      fbText = `💡 Clinical reasoning note:\n${await callClaude([{ role: "user", content: differentials }], sys, 250)}`;
    }
    addMsg(fbText, "lab_tutor");
    setPhase("tests");
    setInputMode("history");
    setBusy(false);
  };

  const submitInterpretation = async () => {
    if (!interpText.trim() || busy) return;
    setBusy(true);
    addMsg(`📊 My interpretation:\n${interpText}`, "lab_note");
    const sys = `${makeTutorPrompt(selCase, "interpretation", mode)}\n\nEvaluate this test interpretation from a medical student. Highlight what is correct and gently redirect any errors. End with a brief question that nudges them toward the next step. 3–5 sentences. Warm and constructive.`;
    try {
      const fb = await callClaude([{ role: "user", content: interpText }], sys, 300);
      addMsg(fb, "lab_tutor");
      setInterpResult(fb);
      setInputMode("history");
    } catch {
      addMsg("⚠ Connection error. Please try again.", "lab_note");
      setInterpResult("⚠ Connection error. Please try again.");
    }
    setBusy(false);
  };

  const submitFinalAnswer = async () => {
    if (!finalAnswer.diagnosis.trim() || busy) return;
    setBusy(true);
    const ansText = `Diagnosis: ${finalAnswer.diagnosis}\nSupporting findings: ${finalAnswer.findings}\nDifferentials: ${finalAnswer.differentials}\nAdditional tests: ${finalAnswer.tests}\nManagement: ${finalAnswer.management}\nGenetic counselling: ${finalAnswer.genetics}\nExplanation to parent: ${finalAnswer.explanation}`;
    addMsg(`✅ Final answer submitted:\n${ansText}`, "student");
    const sys = `${makeFeedbackPrompt(selCase)}\n\nStudent's final answer:\n${ansText}`;
    setActiveTab("consultation");
    try {
      const rawFb = await callClaude([{ role: "user", content: ansText }], sys, 1500);
      const jsonMatch = rawFb.match(/\{[\s\S]*\}/);
      const parsed = JSON.parse(jsonMatch ? jsonMatch[0] : rawFb.trim());
      setFeedback(parsed);
      setPhase("feedback");
    } catch (e) {
      addMsg("⚠ Could not generate structured feedback. Please try again.", "system");
    }
    setBusy(false);
  };

  const getHint = async () => {
    if (busy) return;
    setBusy(true);
    setShowHintMenu(false);
    setHintsUsed(n => n + 1);

    // Build a context summary of what the student has done so far
    const parentExchange = msgs.filter(m => m.type === "parent").length;
    const studentQuestions = msgs.filter(m => m.type === "student").map(m => m.text).join(" | ");
    const orderedList = [...orderedTests];
    const notYetOrdered = Object.keys(selCase.labData).filter(k => !orderedList.some(o => k.toLowerCase().includes(o.toLowerCase()) || o.toLowerCase().includes(k.toLowerCase())));
    const importantMissing = selCase.keyClues.filter(clue => {
      const clueWords = clue.toLowerCase().split(" ").filter(w => w.length > 4);
      return !studentQuestions.toLowerCase().includes(clueWords[0]) && !orderedList.some(t => clueWords.some(w => t.toLowerCase().includes(w)));
    });

    const context = `
CASE: ${selCase.title}
TARGET DIAGNOSIS: ${selCase.targetDiagnosis}
CURRENT PHASE: ${phase}
PARENT EXCHANGES SO FAR: ${parentExchange}
STUDENT HAS ASKED ABOUT: ${studentQuestions || "nothing yet"}
TESTS ORDERED SO FAR: ${orderedList.length > 0 ? orderedList.join(", ") : "none"}
TESTS NOT YET ORDERED (available in this case): ${notYetOrdered.slice(0, 8).join(", ")}
KEY CLUES NOT YET FOUND: ${importantMissing.slice(0, 3).join("; ")}
HINTS USED SO FAR: ${hintsUsed}
    `.trim();

    const sys = `You are a supportive clinical tutor giving a CONTEXTUAL HINT to a medical student who is stuck.

${context}

HINT RULES:
- Give ONE specific, actionable hint based on what the student has NOT yet done
- Do NOT reveal the diagnosis directly
- Do NOT say "the diagnosis is..."
- Scale specificity to hints used: first hint = broad direction; second = specific gap; third = name the single most important missing test or history point
- If no tests have been ordered yet → suggest a test CATEGORY (not a specific name) that would help, e.g. "What basic blood tests would you order for any child with recurrent infections?"
- If some tests ordered but key ones missing → hint toward the gap, e.g. "You have checked the basic bloods — what does the immunology tell you about specific immune compartments?"
- If tests done but history thin → point to the missing history element
- If in differential phase → ask a Socratic question that narrows the field
- Keep the hint to 2–4 sentences. Warm, encouraging tone. Never say "wrong."`;

    try {
      const reply = await callClaude([{ role: "user", content: "I need a hint." }], sys, 200);
      setHintPopup(reply);
    } catch (e) {
      setHintPopup("Think about which immune compartment is most likely affected given the type of infections. Then consider which basic blood tests would characterise that compartment.");
    }
    setBusy(false);
  };

  // ── REFLECTION ──────────────────────────────────────────────────────────────
  const REFLECTION_QS = [
    "What was your initial diagnosis when you first heard the case opening?",
    "Which specific finding or test result changed your thinking most significantly?",
    "Was there a moment where you felt uncertain or stuck? What helped you move forward?",
    "What would you do differently if you encountered this case again?",
    "What is the single most important clinical or scientific concept you will take away from this case?",
  ];

  const submitReflection = async () => {
    if (busy || !input.trim()) return;
    const ans = input.trim();
    setInput("");
    const newAnswers = [...reflectionAnswers, { q: REFLECTION_QS[reflectionStep], a: ans }];
    setReflectionAnswers(newAnswers);
    if (reflectionStep < REFLECTION_QS.length - 1) {
      setReflectionStep(reflectionStep + 1);
    } else {
      setBusy(true);
      const sys = `You are summarising a medical student's reflection on a clinical case: "${selCase.title}" (target diagnosis: ${selCase.targetDiagnosis}). Write 3–4 supportive sentences summarising their reflective reasoning and identifying 1–2 key learning moments. Encourage continued reflection.`;
      const reflText = newAnswers.map(r => `Q: ${r.q}\nA: ${r.a}`).join("\n\n");
      const summary = await callClaude([{ role: "user", content: reflText }], sys, 300);
      setScreen("reflection_done");
      addMsg(summary, "tutor");
      setBusy(false);
    }
  };

  // ── STYLES ─────────────────────────────────────────────────────────────────
  const S = {
    root: { fontFamily: "'Crimson Pro', 'Georgia', serif", background: C.bg, minHeight: "100vh", color: C.text },
    // Welcome screen
    welcome: { maxWidth: 780, margin: "0 auto", padding: "48px 24px" },
    logo: { fontSize: 13, letterSpacing: "0.2em", textTransform: "uppercase", color: C.dim, marginBottom: 8 },
    heroTitle: { fontSize: 44, fontWeight: 700, color: C.navy, lineHeight: 1.15, marginBottom: 12 },
    heroSub: { fontSize: 18, color: C.muted, lineHeight: 1.6, marginBottom: 40 },
    modeCard: (active) => ({ padding: "20px 24px", border: `2px solid ${active ? C.navy : C.border}`, borderRadius: 8, cursor: "pointer", background: active ? C.navyPale : C.surface, marginBottom: 12, transition: "all 0.15s" }),
    caseCard: { padding: "16px 20px", border: `1px solid ${C.border}`, borderRadius: 8, cursor: "pointer", background: C.surface, marginBottom: 10, transition: "all 0.15s" },
    tag: (color) => ({ display: "inline-block", fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", padding: "2px 8px", borderRadius: 4, background: color === "adv" ? C.redPale : color === "int" ? C.amberPale : C.tealPale, color: color === "adv" ? C.red : color === "int" ? C.amber : C.teal }),
    // Chat
    chatWrap: { display: "flex", flexDirection: "column", height: "100vh" },
    chatTop: { background: C.surface, borderBottom: `1px solid ${C.border}`, padding: "10px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 },
    phaseBar: { display: "flex", gap: 0, background: C.surfaceAlt, borderBottom: `1px solid ${C.border}`, overflowX: "auto", flexShrink: 0 },
    phaseItem: (active, done) => ({ padding: "7px 14px", fontSize: 12, letterSpacing: "0.05em", cursor: done ? "pointer" : "default", borderRight: `1px solid ${C.border}`, background: active ? C.navy : "transparent", color: active ? "#fff" : done ? C.teal : C.dim, fontWeight: active ? 600 : 400, whiteSpace: "nowrap", flexShrink: 0 }),
    msgs: { flex: 1, overflowY: "auto", padding: "16px 20px", display: "flex", flexDirection: "column", gap: 12 },
    bubble: (type) => {
      const configs = {
        parent: { bg: C.parentBg, border: C.parentBorder, color: C.parent, label: "👩 Parent", align: "flex-start", maxW: "75%" },
        tutor: { bg: C.tutorBg, border: C.tutorBorder, color: C.tutor, label: "🎓 Clinical tutor", align: "flex-start", maxW: "82%" },
        safety: { bg: C.safetyBg, border: C.safetyBorder, color: C.safety, label: "⚠ Safety alert", align: "flex-start", maxW: "85%" },
        student: { bg: C.studentBg, border: C.studentBorder, color: C.student, label: "You", align: "flex-end", maxW: "72%" },
        system: { bg: C.surfaceAlt, border: C.borderDark, color: C.textLight, label: "", align: "flex-start", maxW: "90%" },
      };
      return configs[type] || configs.system;
    },
    inputArea: { padding: "12px 16px", background: C.surface, borderTop: `1px solid ${C.border}`, flexShrink: 0 },
    input: { width: "100%", border: `1px solid ${C.border}`, borderRadius: 6, padding: "9px 12px", fontSize: 15, fontFamily: "'Crimson Pro', Georgia, serif", color: C.text, background: C.surface, outline: "none", resize: "none", boxSizing: "border-box" },
    btnPrimary: { padding: "8px 18px", background: C.navy, color: "#fff", border: "none", borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: "pointer", letterSpacing: "0.03em" },
    btnSecondary: { padding: "7px 14px", background: "transparent", color: C.navy, border: `1px solid ${C.navy}`, borderRadius: 6, fontSize: 12.5, cursor: "pointer", letterSpacing: "0.02em" },
    btnGhost: { padding: "7px 14px", background: "transparent", color: C.muted, border: `1px solid ${C.border}`, borderRadius: 6, fontSize: 12.5, cursor: "pointer" },
    // Feedback
    feedbackWrap: { maxWidth: 820, margin: "0 auto", padding: "32px 24px" },
    scoreGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 },
    scoreBadge: (v) => ({ padding: "5px 10px", borderRadius: 5, fontSize: 12, fontWeight: 600, background: v === "Excellent" ? C.tealPale : v === "Good" ? C.navyPale : v === "Developing" ? C.amberPale : C.redPale, color: v === "Excellent" ? C.teal : v === "Good" ? C.navy : v === "Developing" ? C.amber : C.red }),
  };

  // ── WELCOME SCREEN ──────────────────────────────────────────────────────────
  if (screen === "welcome") {
    const unseenCount = CASES.filter(c => !seenCases.includes(c.id)).length;
    const completedCount = seenCases.length;
    return (
    <div style={S.root}>
      <div style={{ ...S.welcome, maxWidth: 680 }}>

        {/* Header */}
        <div style={{ marginBottom: 32 }}>
          <div style={S.logo}>Rīga Stradiņš University · Faculty of Medicine</div>
          <h1 style={{ ...S.heroTitle, fontSize: 36 }}>Clinical Immunology</h1>
          <div style={{ fontSize: 20, fontWeight: 600, color: C.teal, marginBottom: 16 }}>Immunology Department — Outpatient Clinic Simulator</div>
          <p style={{ fontSize: 15.5, color: C.muted, lineHeight: 1.7, margin: 0 }}>
            You are a junior doctor working a session at the Immunology Department outpatient clinic. Patients with suspected inborn errors of immunity have been referred to you. Your task is to take a thorough history, examine the patient, order appropriate investigations, form a differential diagnosis, and propose a management plan.
          </p>
        </div>

        {/* How it works */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: "20px 24px", marginBottom: 28 }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: C.navy, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 14 }}>How the session works</div>
          {[
            ["1", "A patient is presented to you with a brief clinical description, similar to what you might observe when they first enter your consulting room."],
            ["2", "You take the history by asking questions directly to the parent or patient. They will only provide information in response to the questions you ask, so the more targeted your questions are, the more relevant information you will gather."],
            ["3", "You may request a physical examination at any time by specifying what you would like to examine."],
            ["4", "You can order investigations in the Investigations tab, shown in the panel above. Results will appear as they would in clinical practice. You may interpret the findings and use them to develop a differential diagnosis."],
            ["5", "When you feel ready, submit your final diagnosis and management plan. The simulator will then provide structured formative feedback on your clinical reasoning."],
            ["6", "Each patient you see in a session will be different. The same case will not appear again until you have worked through all available cases."],
          ].map(([n, text]) => (
            <div key={n} style={{ display: "flex", gap: 12, marginBottom: 11 }}>
              <div style={{ width: 22, height: 22, borderRadius: "50%", background: C.navy, color: "#fff", fontSize: 12, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: 1 }}>{n}</div>
              <div style={{ fontSize: 14, color: C.textLight, lineHeight: 1.6 }}>{text}</div>
            </div>
          ))}
        </div>

        {/* Safe environment */}
        <div style={{ background: C.tealPale, border: `1px solid ${C.teal}`, borderRadius: 8, padding: "12px 16px", marginBottom: 28, fontSize: 14, color: C.teal, lineHeight: 1.6 }}>
          🌿 <strong>Safe learning environment.</strong> You are encouraged to form hypotheses, make mistakes, change your mind, and learn from the consequences. There are no wrong questions. The goal is to practise clinical reasoning, not to guess the correct answer immediately.
        </div>

        {/* Mode selection */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ fontWeight: 700, fontSize: 14, color: C.navy, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 14 }}>Choose your session mode</div>
          {[
            ["practice", "With clinical guidance", "The tutor gives gentle prompts when you submit answers. Contextual hints available any time. Recommended for first attempts."],
            ["exam",     "Independent — minimal guidance", "Fewer proactive prompts from the tutor. Contextual hints still available if you get stuck. Full structured feedback at the end."],
            ["reflection","Reflection mode",        "After completing a case, the simulator asks five reflective questions about your reasoning. Best used after practice or exam mode."],
          ].map(([m, label, desc]) => (
            <div key={m} style={{ ...S.modeCard(mode === m), marginBottom: 10 }} onClick={() => setMode(m)}>
              <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <div style={{ width: 18, height: 18, borderRadius: "50%", border: `2px solid ${C.navy}`, background: mode === m ? C.navy : "transparent", flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15, color: C.navy }}>{label}</div>
                  <div style={{ fontSize: 13, color: C.muted, marginTop: 3, lineHeight: 1.5 }}>{desc}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Progress indicator */}
        {storageLoaded && completedCount > 0 && (
          <div style={{ background: C.navyPale, border: `1px solid ${C.border}`, borderRadius: 8, padding: "10px 16px", marginBottom: 20, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <span style={{ fontSize: 13, color: C.navy, fontWeight: 600 }}>Session progress: </span>
              <span style={{ fontSize: 13, color: C.muted }}>{completedCount} of {CASES.length} cases seen</span>
              <div style={{ display: "flex", gap: 5, marginTop: 6 }}>
                {CASES.map(c => (
                  <div key={c.id} style={{ width: 28, height: 6, borderRadius: 3, background: seenCases.includes(c.id) ? C.teal : C.border }} title={c.title} />
                ))}
              </div>
            </div>
            <button style={{ ...S.btnGhost, fontSize: 12 }} onClick={resetProgress}>Reset</button>
          </div>
        )}

        {/* All done state */}
        {allDone && (
          <div style={{ background: C.amberPale, border: `1px solid ${C.amber}`, borderRadius: 8, padding: "14px 18px", marginBottom: 20, fontSize: 14, color: C.amber, lineHeight: 1.6 }}>
            🎉 <strong>You have seen all {CASES.length} available cases.</strong> Reset your progress to start again, or browse individual cases below.
          </div>
        )}

        {/* Main action button */}
        <button
          style={{ width: "100%", padding: "16px 24px", background: allDone ? C.border : C.navy, color: allDone ? C.dim : "#fff", border: "none", borderRadius: 8, fontSize: 17, fontWeight: 700, cursor: allDone ? "default" : "pointer", letterSpacing: "0.02em", marginBottom: 14, fontFamily: "'Crimson Pro', Georgia, serif" }}
          onClick={startRandomCase}
          disabled={allDone || !storageLoaded}
        >
          {!storageLoaded ? "Loading…" : allDone ? "All cases completed" : unseenCount === CASES.length ? "See next patient →" : `See next patient → (${unseenCount} remaining)`}
        </button>

        {/* Browse option */}
        <div style={{ textAlign: "center" }}>
          <button style={{ ...S.btnGhost, fontSize: 13 }} onClick={() => setShowBrowse(!showBrowse)}>
            {showBrowse ? "Hide case list ↑" : "Browse cases individually ↓"}
          </button>
        </div>

        {showBrowse && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, color: C.muted, marginBottom: 10, fontStyle: "italic" }}>Note: selecting a specific case manually will not mark it as seen in your progress.</div>
            {CASES.map(c => (
              <div key={c.id} style={{ ...S.caseCard, opacity: seenCases.includes(c.id) ? 0.6 : 1 }}
                onClick={() => startCase(c)}
                onMouseEnter={e => e.currentTarget.style.borderColor = C.navy}
                onMouseLeave={e => e.currentTarget.style.borderColor = C.border}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 15, color: C.navy, marginBottom: 2 }}>{c.title}</div>
                    <div style={{ fontSize: 12.5, color: C.muted }}>{c.patient} · {c.topic}</div>
                  </div>
                  <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                    {seenCases.includes(c.id) && <span style={{ fontSize: 11, color: C.teal, fontWeight: 600 }}>✓ seen</span>}
                    <span style={S.tag(c.difficulty === "Advanced" ? "adv" : c.difficulty === "Intermediate" ? "int" : "beg")}>{c.difficulty}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
    );
  }


  // ── REFLECTION DONE ─────────────────────────────────────────────────────────
  if (screen === "reflection_done") return (
    <div style={S.root}>
      <div style={{ maxWidth: 600, margin: "0 auto", padding: "48px 24px" }}>
        <h2 style={{ fontSize: 28, fontWeight: 700, color: C.navy, marginBottom: 24 }}>Reflection complete</h2>
        {msgs.filter(m => m.type === "tutor").slice(-1).map((m, i) => (
          <div key={i} style={{ background: C.tutorBg, border: `1px solid ${C.tutorBorder}`, borderRadius: 8, padding: "16px 20px", fontSize: 15, lineHeight: 1.7, color: C.tutor, marginBottom: 24 }}>{m.text}</div>
        ))}
        <div style={{ background: C.tealPale, border: `1px solid ${C.teal}`, borderRadius: 8, padding: "12px 16px", fontSize: 14, color: C.teal, marginBottom: 24 }}>
          You can return to this case at any time, or explore another case from the library.
        </div>
        <button style={S.btnPrimary} onClick={() => { setScreen("welcome"); setAllDone(false); }}>Return to clinic</button>
      </div>
    </div>
  );

  // ── CHAT SCREEN ─────────────────────────────────────────────────────────────
  if (screen !== "chat") return null;
  const phaseIdx = PHASE_ORDER.indexOf(phase);
  const labMsgs = msgs.filter(m => m.type === "lab");
  const investMsgs = msgs.filter(m => m.type === "lab" || m.type === "lab_note" || m.type === "lab_tutor");
  const chatMsgs = msgs.filter(m => m.type !== "lab" && m.type !== "lab_note" && m.type !== "lab_tutor");

  return (
    <div style={S.chatWrap}>
      {/* Header */}
      <div style={S.chatTop}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: C.navy }}>{selCase.title}</div>
          <div style={{ fontSize: 12, color: C.muted }}>{selCase.patient} · {selCase.topic} · {mode === "practice" ? "Practice Mode" : mode === "exam" ? "Exam Mode" : "Reflection Mode"}</div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {phase !== "feedback" && phase !== "reflection" && (
            <div style={{ position: "relative" }}>
              <button
                style={{ ...S.btnSecondary, opacity: busy ? 0.5 : 1 }}
                onClick={() => setShowHintMenu(h => !h)}
                disabled={busy}
              >
                💡 Need a hint{hintsUsed > 0 ? ` (${hintsUsed} used)` : ""}
              </button>
              {showHintMenu && (
                <div style={{ position:"absolute", right:0, top:"110%", background:C.surface, border:`1px solid ${C.border}`, borderRadius:10, padding:14, zIndex:50, width:260, boxShadow:"0 4px 16px rgba(0,0,0,0.12)" }}>
                  <div style={{ fontSize:13, fontWeight:600, color:C.navy, marginBottom:6 }}>Ask for guidance</div>
                  <div style={{ fontSize:12, color:C.muted, marginBottom:12, lineHeight:1.5 }}>
                    The hint is personalised — it looks at what you have already asked and ordered, and points toward what might be missing.
                  </div>
                  <button style={{ ...S.btnPrimary, width:"100%", fontSize:13 }} onClick={getHint}>
                    Get a contextual hint →
                  </button>
                  {hintsUsed > 0 && (
                    <div style={{ fontSize:11, color:C.dim, textAlign:"center", marginTop:8 }}>
                      {hintsUsed} hint{hintsUsed > 1 ? "s" : ""} used this case
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          {hintPopup && (
            <>
              <div onClick={() => setHintPopup(null)} style={{ position:"fixed", inset:0, background:"rgba(0,0,0,0.35)", zIndex:999 }} />
              <div style={{ position:"fixed", top:"50%", left:"50%", transform:"translate(-50%,-50%)", width:"min(320px, 90%)", background:"#EEF2FB", border:"1px solid #B0C0E0", borderRadius:10, padding:"14px 16px", boxShadow:"0 8px 32px rgba(0,0,0,0.2)", zIndex:1000, fontFamily:"'Segoe UI',Arial,sans-serif" }}>
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:8 }}>
                  <div style={{ fontSize:9.5, fontWeight:700, color:"#1A2B5A", letterSpacing:"0.08em", textTransform:"uppercase", opacity:0.65 }}>🎓 Clinical tutor</div>
                  <button onClick={() => setHintPopup(null)} style={{ background:"none", border:"none", cursor:"pointer", fontSize:14, color:"#6B6560", lineHeight:1, padding:0 }}>✕</button>
                </div>
                <div style={{ fontSize:13, lineHeight:1.65, color:"#1A2B5A" }}>{hintPopup}</div>
                <button onClick={() => setHintPopup(null)} style={{ marginTop:10, padding:"6px 16px", background:"#1A2B4A", color:"#fff", border:"none", borderRadius:6, fontSize:12, fontWeight:600, cursor:"pointer", fontFamily:"inherit" }}>Got it</button>
              </div>
            </>
          )}
          <button style={S.btnGhost} onClick={() => { setScreen("welcome"); setAllDone(false); }}>← Exit to clinic</button>
        </div>
      </div>
      {/* Phase bar */}
      <div style={S.phaseBar}>
        {PHASE_ORDER.map((p, i) => (
          <div key={p} style={S.phaseItem(phase === p, i < phaseIdx)}>
            {i < phaseIdx ? "✓ " : ""}{PHASE_LABELS[p]}
          </div>
        ))}
      </div>

      {/* ── TAB BAR ── */}
      <div style={{ display:"flex", background:C.surface, borderBottom:`2px solid ${C.border}`, flexShrink:0 }}>
        {[
          { key:"consultation",  label:"💬 Consultation" },
          { key:"investigations", label:"🔬 Investigations", badge: labMsgs.length },
          { key:"diagnosis",     label:"📋 Final Diagnosis" },
        ].map(({ key, label, badge }) => (
          <button key={key} onClick={() => setActiveTab(key)}
            style={{ padding:"11px 22px", fontSize:13.5,
              fontWeight: activeTab === key ? 700 : 500,
              color: activeTab === key ? C.navy : C.muted,
              background:"transparent", border:"none",
              borderBottom: activeTab === key ? `3px solid ${C.navy}` : "3px solid transparent",
              cursor:"pointer", marginBottom:-2, letterSpacing:"0.01em",
              fontFamily:"'Crimson Pro',Georgia,serif", transition:"color 0.15s" }}>
            {label}
            {badge > 0 && (
              <span style={{ marginLeft:7, background:C.teal, color:"#fff", borderRadius:10,
                fontSize:10, fontWeight:700, padding:"1px 7px", verticalAlign:"middle" }}>
                {badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── TAB CONTENT ── */}
      <div style={{ flex:1, overflow:"hidden", display:"flex", flexDirection:"column" }}>

        {/* ════════════ CONSULTATION TAB ════════════ */}
        {activeTab === "consultation" && (
          <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>

            {/* Messages — lab results filtered out; they live in Investigations tab */}
            <div style={S.msgs}>
              {chatMsgs.map((m) => {
                const cfg = S.bubble(m.type);
                return (
                  <div key={m.id} style={{ display:"flex", justifyContent:cfg.align }}>
                    <div style={{ maxWidth:cfg.maxW, background:cfg.bg, border:`1px solid ${cfg.border}`,
                      borderRadius: m.type === "student" ? "12px 12px 4px 12px" : "12px 12px 12px 4px",
                      padding:"10px 14px" }}>
                      {cfg.label && <div style={{ fontSize:10.5, fontWeight:700, color:cfg.color, opacity:0.7, marginBottom:4, letterSpacing:"0.08em", textTransform:"uppercase" }}>{cfg.label}</div>}
                      <div style={{ fontSize:14.5, lineHeight:1.65, color:cfg.color, whiteSpace:"pre-wrap" }}>{m.text}</div>
                    </div>
                  </div>
                );
              })}
              {busy && phase !== "feedback" && (
                <div style={{ display:"flex" }}>
                  <div style={{ background:C.parentBg, border:`1px solid ${C.parentBorder}`, borderRadius:"12px 12px 12px 4px", padding:"10px 14px" }}>
                    <div style={{ fontSize:10.5, fontWeight:700, color:C.parent, opacity:0.7, letterSpacing:"0.08em", textTransform:"uppercase", marginBottom:4 }}>Parent</div>
                    <div style={{ fontSize:14.5, color:C.parent, opacity:0.5 }}>Typing…</div>
                  </div>
                </div>
              )}
              {busy && phase === "feedback" && (
                <div style={{ textAlign:"center", padding:"32px 0", color:C.muted, fontSize:14 }}>
                  Generating feedback report…
                </div>
              )}
              {/* ── FEEDBACK CARD ── */}
              {phase === "feedback" && feedback && (() => {
                const accColor = feedback.diagnosticAccuracy === "correct" ? C.teal : feedback.diagnosticAccuracy === "partially_correct" ? C.amber : C.red;
                return (
                  <div style={{ maxWidth:640, margin:"0 auto", paddingBottom:32 }}>
                    <h2 style={{ fontSize:24, fontWeight:700, color:C.navy, marginBottom:4 }}>Feedback Report</h2>
                    <div style={{ fontSize:13, color:C.muted, marginBottom:20 }}>{selCase.title}</div>
                    <div style={{ background: feedback.diagnosticAccuracy === "correct" ? C.tealPale : feedback.diagnosticAccuracy === "partially_correct" ? C.amberPale : C.redPale, border:`1px solid ${accColor}`, borderRadius:8, padding:"14px 18px", marginBottom:16 }}>
                      <div style={{ fontWeight:700, fontSize:15, color:accColor, marginBottom:4 }}>
                        {feedback.diagnosticAccuracy === "correct" ? "✓ Correct diagnosis" : feedback.diagnosticAccuracy === "partially_correct" ? "◐ Partially correct" : "○ Incorrect diagnosis"}
                      </div>
                      <div style={{ fontSize:14, color:C.textLight }}>{feedback.diagnosticComment}</div>
                    </div>
                    <h3 style={{ fontSize:14, fontWeight:700, color:C.navy, marginBottom:10 }}>Performance overview</h3>
                    <div style={S.scoreGrid}>
                      {Object.entries(feedback.scores || {}).map(([domain, score]) => (
                        <div key={domain} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"7px 10px", background:C.surface, border:`1px solid ${C.border}`, borderRadius:6 }}>
                          <span style={{ fontSize:12.5, color:C.textLight, textTransform:"capitalize" }}>{domain.replace(/([A-Z])/g, " $1").trim()}</span>
                          <span style={S.scoreBadge(score)}>{score}</span>
                        </div>
                      ))}
                    </div>
                    <div style={{ marginTop:18 }}>
                      <h3 style={{ fontSize:14, fontWeight:700, color:C.teal, marginBottom:8 }}>✓ What you did well</h3>
                      {(feedback.wellDone || []).map((p, i) => <div key={i} style={{ padding:"6px 10px", marginBottom:5, background:C.tealPale, borderLeft:`3px solid ${C.teal}`, borderRadius:"0 6px 6px 0", fontSize:13.5, color:C.textLight }}>{p}</div>)}
                    </div>
                    {(feedback.missing || []).length > 0 && (
                      <div style={{ marginTop:16 }}>
                        <h3 style={{ fontSize:14, fontWeight:700, color:C.amber, marginBottom:8 }}>◎ Areas to develop</h3>
                        {feedback.missing.map((p, i) => <div key={i} style={{ padding:"6px 10px", marginBottom:5, background:C.amberPale, borderLeft:`3px solid ${C.amber}`, borderRadius:"0 6px 6px 0", fontSize:13.5, color:C.textLight }}>{p}</div>)}
                      </div>
                    )}
                    <div style={{ marginTop:16 }}>
                      <h3 style={{ fontSize:14, fontWeight:700, color:C.navy, marginBottom:8 }}>🔍 Key diagnostic clues in this case</h3>
                      <div style={{ background:C.navyPale, border:`1px solid ${C.border}`, borderRadius:8, padding:"10px 14px" }}>
                        {(feedback.keyClues || []).map((c, i) => <div key={i} style={{ fontSize:13.5, color:C.textLight, marginBottom:3, paddingLeft:10, borderLeft:`2px solid ${C.navy}` }}>• {c}</div>)}
                      </div>
                    </div>
                    <div style={{ marginTop:16 }}>
                      <h3 style={{ fontSize:14, fontWeight:700, color:C.navy, marginBottom:8 }}>🧭 Ideal reasoning pathway</h3>
                      <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:8, padding:"12px 14px", fontSize:14, lineHeight:1.7, color:C.textLight }}>{feedback.reasoningPathway}</div>
                    </div>
                    <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14, marginTop:16 }}>
                      <div>
                        <h3 style={{ fontSize:13, fontWeight:700, color:C.navy, marginBottom:8 }}>💊 Management learning points</h3>
                        {(feedback.managementPoints || []).map((p, i) => <div key={i} style={{ fontSize:13, color:C.textLight, marginBottom:5, paddingLeft:8, borderLeft:`2px solid ${C.navyLight}` }}>• {p}</div>)}
                      </div>
                      <div>
                        <h3 style={{ fontSize:13, fontWeight:700, color:C.navy, marginBottom:8 }}>🧬 Genetic counselling points</h3>
                        {(feedback.geneticPoints || []).map((p, i) => <div key={i} style={{ fontSize:13, color:C.textLight, marginBottom:5, paddingLeft:8, borderLeft:`2px solid ${C.teal}` }}>• {p}</div>)}
                      </div>
                    </div>
                    <div style={{ marginTop:16, background:C.navyPale, border:`1px solid ${C.border}`, borderRadius:8, padding:"12px 14px" }}>
                      <div style={{ fontWeight:600, fontSize:13.5, color:C.navy, marginBottom:3 }}>📖 Suggested revision</div>
                      <div style={{ fontSize:13.5, color:C.textLight }}>{feedback.revisionTopic}</div>
                    </div>
                    <div style={{ display:"flex", gap:10, marginTop:24, flexWrap:"wrap" }}>
                      <button style={S.btnPrimary} onClick={() => { setScreen("welcome"); setAllDone(false); }}>See next patient</button>
                      {mode !== "reflection" && (
                        <button style={S.btnSecondary} onClick={() => { setMode("reflection"); setPhase("reflection"); }}>Reflect on this case</button>
                      )}
                      <button style={S.btnGhost} onClick={() => { setScreen("welcome"); setAllDone(false); setShowBrowse(true); }}>Browse all cases</button>
                    </div>
                  </div>
                );
              })()}
              <div ref={chatEnd} />
            </div>

            {/* Phase action bar */}
            {["history","summary","examination","differential","tests","interpretation"].includes(phase) && (
              <div style={{ padding:"8px 14px", background:C.surfaceAlt, borderTop:`1px solid ${C.border}`, display:"flex", gap:7, flexWrap:"wrap", alignItems:"center" }}>
                <span style={{ fontSize:11.5, color:C.dim, alignSelf:"center", marginRight:2 }}>Next step:</span>

                {!examDone && msgs.filter(m => m.type === "parent").length >= 2 && (
                  <button style={S.btnSecondary} onClick={requestExam}>🩺 Examine patient</button>
                )}

                {msgs.filter(m => m.type === "parent").length >= 3 && phase === "history" && (
                  <button style={S.btnGhost} onClick={() => {
                    setPhase("summary"); setInputMode("summary_input");
                    addMsg("Please write a clinical summary in 2–4 sentences: main problem, key history features, and your initial thinking about which immune compartment is affected.", "tutor");
                  }}>📝 Submit summary</button>
                )}

                {msgs.filter(m => m.type === "parent").length >= 2 && (
                  <button style={{ ...S.btnSecondary, background:C.navyPale }} onClick={() => setActiveTab("investigations")}>
                    🔬 Order investigations →
                  </button>
                )}

                {orderedTests.size >= 2 && phase === "tests" && (
                  <button style={S.btnSecondary} onClick={() => {
                    setPhase("interpretation"); setInputMode("interp_input");
                    setActiveTab("investigations");
                    addMsg("You have gathered investigation results. Please interpret the key findings — which results are most important, and what do they tell you about the likely diagnosis?", "lab_tutor");
                  }}>📊 Interpret results →</button>
                )}
              </div>
            )}

            {/* Reflection */}
            {phase === "reflection" && screen === "chat" && (
              <div style={{ padding:"16px 20px", background:C.surface, borderTop:`1px solid ${C.border}` }}>
                <div style={{ fontSize:13, color:C.muted, marginBottom:8 }}>Reflection question {reflectionStep + 1} of {REFLECTION_QS.length}:</div>
                <div style={{ fontSize:15, fontWeight:600, color:C.navy, marginBottom:12 }}>{REFLECTION_QS[reflectionStep]}</div>
                <div style={{ display:"flex", gap:8 }}>
                  <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && submitReflection()} style={{ ...S.input, flex:1 }} placeholder="Your reflection..." />
                  <button style={S.btnPrimary} onClick={submitReflection}>→</button>
                </div>
              </div>
            )}

            {/* Summary input */}
            {inputMode === "summary_input" && phase === "summary" && (
              <div style={{ padding:"12px 16px", background:C.surfaceAlt, borderTop:`1px solid ${C.border}` }}>
                <textarea value={summary} onChange={e => setSummary(e.target.value)}
                  placeholder="Write your clinical summary in 2–4 sentences..."
                  style={{ ...S.input, minHeight:80, display:"block", marginBottom:8 }} />
                <button style={S.btnPrimary} onClick={submitSummary} disabled={busy || !summary.trim()}>Submit summary</button>
              </div>
            )}

            {/* Differential input */}
            {inputMode === "diff_input" && phase === "differential" && (
              <div style={{ padding:"12px 16px", background:C.surfaceAlt, borderTop:`1px solid ${C.border}` }}>
                <textarea value={differentials} onChange={e => setDifferentials(e.target.value)}
                  placeholder="State your top 2–3 differential diagnoses..."
                  style={{ ...S.input, minHeight:80, display:"block", marginBottom:8 }} />
                <button style={S.btnPrimary} onClick={submitDifferentials} disabled={busy || !differentials.trim()}>Submit differentials</button>
              </div>
            )}

            {/* Main chat input */}
            {!["summary_input","diff_input","interp_input"].includes(inputMode) && phase !== "reflection" && phase !== "final" && (
              <div style={S.inputArea}>
                <div style={{ display:"flex", gap:8 }}>
                  <textarea value={input} onChange={e => setInput(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendMessage())}
                    rows={2}
                    placeholder="Ask the parent a question…"
                    style={{ ...S.input, flex:1, resize:"none" }}
                    disabled={busy} />
                  <button style={{ ...S.btnPrimary, alignSelf:"flex-end", padding:"10px 18px" }} onClick={sendMessage} disabled={busy || !input.trim()}>Send</button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ════════════ INVESTIGATIONS TAB ════════════ */}
        {activeTab === "investigations" && (
          <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
            <div style={{ flex:1, overflowY:"auto", padding:"16px 20px" }}>
              {investMsgs.length === 0 ? (
                <div style={{ textAlign:"center", maxWidth:440, margin:"64px auto 0" }}>
                  <div style={{ fontSize:44, marginBottom:16 }}>🔬</div>
                  <div style={{ fontSize:16, fontWeight:700, color:C.navy, marginBottom:10 }}>No investigations ordered yet</div>
                  <div style={{ fontSize:14, color:C.muted, lineHeight:1.75 }}>
                    Type test names in the field below and press <strong>Order</strong> — for example:<br />
                    <em>"CBC, CRP, immunoglobulins, chest X-ray"</em>
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ fontSize:12, color:C.dim, marginBottom:14 }}>
                    {orderedTests.size} investigation{orderedTests.size !== 1 ? "s" : ""} ordered
                  </div>
                  {investMsgs.map((m) => {
                    if (m.type === "lab_note") {
                      return (
                        <div key={m.id} style={{ padding:"9px 12px", background:C.surfaceAlt, border:`1px solid ${C.border}`, borderRadius:6, fontSize:13, color:C.textLight, marginBottom:10 }}>
                          {m.text}
                        </div>
                      );
                    }
                    if (m.type === "lab_tutor") {
                      return (
                        <div key={m.id} style={{ background:C.tutorBg, border:`1px solid ${C.tutorBorder}`, borderRadius:8, padding:"12px 16px", marginBottom:12 }}>
                          <div style={{ fontSize:11, fontWeight:700, color:C.tutor, letterSpacing:"0.06em", textTransform:"uppercase", marginBottom:5 }}>🎓 Clinical tutor</div>
                          <div style={{ fontSize:14, color:C.tutor, lineHeight:1.7 }}>{m.text}</div>
                        </div>
                      );
                    }
                    const [header, ...rest] = m.text.replace("__LAB__","").split("\n");
                    const bodyText = rest.join(" ");
                    const rows = parseLabText(bodyText);
                    const hasRows = rows.some(r => r.type === "row");
                    return (
                      <div key={m.id} style={{ marginBottom:14 }}>
                        <div style={{ background:"#ffffff", border:"1px solid #C8D8E8", borderRadius:8, overflow:"hidden", fontFamily:"'DM Sans','Segoe UI',sans-serif" }}>
                          <div style={{ background:"#EDF2F8", padding:"7px 14px", display:"flex", alignItems:"center", gap:8, borderBottom:"1px solid #C8D8E8" }}>
                            <span style={{ fontSize:13 }}>🔬</span>
                            <span style={{ fontSize:12, fontWeight:700, color:"#1A2B4A", letterSpacing:"0.05em", textTransform:"uppercase" }}>{header}</span>
                          </div>
                          {hasRows && (
                            <table style={{ width:"100%", borderCollapse:"collapse" }}>
                              <thead>
                                <tr style={{ background:"#F5F8FC" }}>
                                  <th style={{ padding:"5px 12px", fontSize:10.5, fontWeight:700, color:"#5A6A80", textAlign:"left", letterSpacing:"0.08em", textTransform:"uppercase", width:"42%", borderBottom:"1px solid #D8E4EE" }}>Parameter</th>
                                  <th style={{ padding:"5px 12px", fontSize:10.5, fontWeight:700, color:"#5A6A80", textAlign:"left", letterSpacing:"0.08em", textTransform:"uppercase", borderBottom:"1px solid #D8E4EE" }}>Result</th>
                                </tr>
                              </thead>
                              <tbody>
                                {rows.map((row, ri) => {
                                  if (row.type === "note") {
                                    return (
                                      <tr key={ri} style={{ background:"#FFFBF0" }}>
                                        <td colSpan={2} style={{ padding:"6px 12px", fontSize:12, color:"#7B4A00", lineHeight:1.5, fontStyle:"italic", borderTop:"1px solid #EEE0C0" }}>
                                          ⚠ {row.text}
                                        </td>
                                      </tr>
                                    );
                                  }
                                  const flag = flagRow(row.value);
                                  const fs = FLAG_STYLE[flag];
                                  const rowBg = fs.bg !== "transparent" ? fs.bg : ri % 2 === 0 ? "#ffffff" : "#F8FAFC";
                                  return (
                                    <tr key={ri} style={{ background:rowBg }}>
                                      <td style={{ padding:"7px 12px", fontSize:13, color:"#2A3A4A", fontWeight:500, borderRight:"1px solid #D8E4EE", verticalAlign:"top", lineHeight:1.5 }}>
                                        {row.param}
                                      </td>
                                      <td style={{ padding:"7px 12px", fontSize:13, color:fs.text, fontWeight:fs.bg !== "transparent" ? 600 : 400, lineHeight:1.5, verticalAlign:"top" }}>
                                        {row.value}
                                        {fs.badge && (
                                          <span style={{ marginLeft:7, fontSize:10, fontWeight:800, padding:"1px 6px", borderRadius:3, background:fs.badgeBg, color:fs.badgeText, verticalAlign:"middle", letterSpacing:"0.04em" }}>
                                            {fs.badge}
                                          </span>
                                        )}
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          )}
                          {!hasRows && (
                            <div style={{ padding:"10px 14px" }}>
                              {rows.map((row, ri) => (
                                <div key={ri} style={{ fontSize:13, color:"#2A3A4A", lineHeight:1.6, marginBottom:2 }}>{row.text}</div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  <div ref={labEnd} />
                </div>
              )}
            </div>

            {/* Propose differentials — appears after ≥3 lab results */}
            {labMsgs.length >= 3 && !["differential","final","feedback"].includes(phase) && (
              <div style={{ padding:"10px 18px", background:C.tealPale, borderTop:`1px solid ${C.teal}`, display:"flex", justifyContent:"space-between", alignItems:"center", flexShrink:0 }}>
                <div style={{ fontSize:13, color:C.teal, fontWeight:600 }}>You have enough results to form a differential.</div>
                <button style={{ ...S.btnSecondary, borderColor:C.teal, color:C.teal }} onClick={() => {
                  setPhase("differential"); setInputMode("diff_input");
                  setActiveTab("consultation");
                  addMsg("Please state your top 2–3 differential diagnoses or immune defect categories. Consider which immune compartment is most likely affected.", "tutor");
                }}>📋 Propose differentials</button>
              </div>
            )}

            {/* Interpret results prompt — once enough tests ordered */}
            {orderedTests.size >= 2 && !["interpretation","final","feedback"].includes(phase) && (
              <div style={{ padding:"10px 18px", background:C.navyPale, borderTop:`1px solid ${C.border}`, display:"flex", justifyContent:"space-between", alignItems:"center", flexShrink:0 }}>
                <div style={{ fontSize:13, color:C.navy, fontWeight:600 }}>Ready to interpret your results?</div>
                <button style={S.btnPrimary} onClick={() => {
                  setPhase("interpretation"); setInputMode("interp_input");
                  addMsg("You have gathered investigation results. Please interpret the key findings — which results are most important, and what do they tell you about the likely diagnosis?", "lab_tutor");
                }}>→ Interpret results</button>
              </div>
            )}

            {/* Interpretation input / result — stays in Investigations tab */}
            {phase === "interpretation" && inputMode === "interp_input" ? (
              <div style={{ padding:"14px 18px", background:C.surfaceAlt, borderTop:`1px solid ${C.border}`, flexShrink:0 }}>
                <div style={{ fontSize:12, color:C.dim, marginBottom:6 }}>Interpret your findings — write your reasoning below</div>
                <textarea value={interpText} onChange={e => setInterpText(e.target.value)}
                  placeholder="Which results are most significant? What do they tell you about the likely diagnosis?"
                  style={{ ...S.input, minHeight:90, display:"block", marginBottom:8, resize:"vertical" }} />
                <button style={S.btnPrimary} onClick={submitInterpretation} disabled={busy || !interpText.trim()}>Submit interpretation</button>
              </div>
            ) : interpResult ? (
              /* Tutor feedback after interpretation */
              <div style={{ padding:"14px 18px", background:C.surfaceAlt, borderTop:`1px solid ${C.border}`, flexShrink:0 }}>
                <div style={{ background:C.tutorBg, border:`1px solid ${C.tutorBorder}`, borderRadius:8, padding:"12px 16px", marginBottom:10 }}>
                  <div style={{ fontSize:11, fontWeight:700, color:C.tutor, letterSpacing:"0.06em", textTransform:"uppercase", marginBottom:5 }}>🎓 Clinical tutor</div>
                  <div style={{ fontSize:14, color:C.tutor, lineHeight:1.7 }}>{interpResult}</div>
                </div>
                <div style={{ fontSize:11, color:C.muted, marginBottom:7 }}>What would you like to do next?</div>
                <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                  <button style={S.btnPrimary} onClick={() => {
                    setPhase("final"); setShowFinalForm(true); setActiveTab("diagnosis");
                    addMsg("Please now submit your final diagnosis and management plan.", "lab_tutor");
                  }}>→ Submit final answer</button>
                  <button style={S.btnSecondary} onClick={() => setActiveTab("consultation")}>
                    ← Ask the parent more questions
                  </button>
                  <button style={S.btnGhost} onClick={() => {
                    setInterpText(""); setInterpResult(""); setInputMode("interp_input"); setPhase("tests");
                  }}>Order more tests</button>
                </div>
              </div>
            ) : (
              /* Test ordering input */
              <div style={S.inputArea}>
                <div style={{ fontSize:12, color:C.dim, marginBottom:5 }}>Order a test — type name(s) and press Enter or Order</div>
                <div style={{ display:"flex", gap:8 }}>
                  <textarea value={input} onChange={e => setInput(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendTestOrder())}
                    rows={2}
                    placeholder={`e.g. "CBC, CRP, immunoglobulins, chest X-ray, flow cytometry"`}
                    style={{ ...S.input, flex:1, resize:"none" }}
                    disabled={busy} />
                  <button style={{ ...S.btnPrimary, alignSelf:"flex-end", padding:"10px 18px" }} onClick={sendTestOrder} disabled={busy || !input.trim()}>Order</button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ════════════ FINAL DIAGNOSIS TAB ════════════ */}
        {activeTab === "diagnosis" && (
          <div style={{ flex:1, overflowY:"auto", padding:"20px 28px" }}>
            {!showFinalForm ? (
              <div style={{ textAlign:"center", maxWidth:480, margin:"52px auto 0" }}>
                <div style={{ fontSize:44, marginBottom:16 }}>📋</div>
                <div style={{ fontSize:18, fontWeight:700, color:C.navy, marginBottom:10 }}>Final Diagnosis</div>
                <div style={{ fontSize:14, color:C.muted, lineHeight:1.75, marginBottom:28 }}>
                  Complete your consultation, examine the patient, and order investigations before submitting your final diagnosis. When you are ready, click below.
                </div>
                {(orderedTests.size >= 1 || examDone) ? (
                  <button style={{ ...S.btnPrimary, padding:"12px 32px", fontSize:15 }} onClick={() => {
                    setPhase("final"); setShowFinalForm(true);
                    addMsg("Please now submit your final diagnosis and management plan.", "tutor");
                  }}>
                    → Submit final diagnosis
                  </button>
                ) : (
                  <div style={{ fontSize:13, color:C.amber, background:C.amberPale, border:`1px solid ${C.amber}`, borderRadius:8, padding:"12px 18px" }}>
                    Please take a history and order at least one investigation before submitting a diagnosis.
                  </div>
                )}
              </div>
            ) : (
              <div>
                <div style={{ fontSize:16, fontWeight:700, color:C.navy, marginBottom:20 }}>Submit your final answer</div>
                {[
                  ["diagnosis",    "Most likely diagnosis"],
                  ["findings",     "Main supporting findings (3–5 bullet points)"],
                  ["differentials","Differential diagnoses"],
                  ["tests",        "Additional tests or confirmatory testing"],
                  ["management",   "Initial management plan"],
                  ["genetics",     "Genetic counselling and family implications"],
                  ["explanation",  "How would you explain this to the parent?"],
                ].map(([k, label]) => (
                  <div key={k} style={{ marginBottom:12 }}>
                    <div style={{ fontSize:12.5, fontWeight:600, color:C.muted, marginBottom:4 }}>{label}</div>
                    <textarea value={finalAnswer[k]} onChange={e => setFinalAnswer(f => ({ ...f, [k]: e.target.value }))}
                      rows={k === "explanation" ? 3 : 2}
                      style={{ ...S.input, display:"block" }} />
                  </div>
                ))}
                <button style={{ ...S.btnPrimary, marginTop:10, padding:"10px 28px" }} onClick={submitFinalAnswer} disabled={busy || !finalAnswer.diagnosis.trim()}>
                  {busy ? "Generating feedback…" : "Submit final answer"}
                </button>
              </div>
            )}
          </div>
        )}

      </div>{/* end tab content */}
    </div>
  );
}
