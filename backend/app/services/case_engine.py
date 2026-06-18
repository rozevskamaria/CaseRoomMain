import re


def parse_lab_text(text):
    normalized = re.sub(r"\. NOTE:", "\nNOTE:", text, flags=re.IGNORECASE)
    normalized = re.sub(r"\. ⚠", "\n⚠", normalized)
    normalized = re.sub(r"\. KEY:", "\nKEY:", normalized, flags=re.IGNORECASE)
    parts = re.split(r"\.\s+(?=[A-Z])", normalized)
    raw = [
        cleaned
        for cleaned in (re.sub(r"\.$", "", s.strip()).strip() for s in parts)
        if cleaned
    ]

    rows = []
    for sentence in raw:
        if re.match(r"^(NOTE|⚠|KEY|IMPORTANT|WARNING)[:!]", sentence, flags=re.IGNORECASE):
            rows.append({
                "type": "note",
                "text": re.sub(
                    r"^(NOTE|⚠|KEY|IMPORTANT|WARNING)[:!]\s*",
                    "",
                    sentence,
                    flags=re.IGNORECASE,
                ),
            })
            continue
        colon_idx = sentence.find(":")
        if 0 < colon_idx < 60:
            rows.append({
                "type": "row",
                "param": sentence[:colon_idx].strip(),
                "value": sentence[colon_idx + 1:].strip(),
            })
            continue
        m = re.match(
            r"^([A-Za-z][A-Za-z0-9+\-\/\s]{0,35}?)\s+([<>≤≥~]?[\d\.,]+.*)\Z",
            sentence,
        )
        if m:
            rows.append({
                "type": "row",
                "param": m.group(1).strip(),
                "value": m.group(2).strip(),
            })
            continue
        rows.append({"type": "note", "text": sentence})
    return rows


def flag_row(value):
    v = value.upper()
    if re.search(r"↑↑↑|CRITICALLY", v):
        return "crit"
    if re.search(r"↑↑|MARKEDLY ELEVATED", v):
        return "hi2"
    if re.search(r"↑|ELEVATED|HIGH|POSITIVE(?! FOR)|RAISED", v):
        return "hi"
    if re.search(r"ABSENT|UNDETECTABLE|0\.0%|VIRTUALLY ABSENT", v):
        return "absent"
    if re.search(r"DIAGNOSTIC|PATHOGNOMONIC", v):
        return "diag"
    if re.search(r"↓↓↓|SEVERELY (LOW|DECREASED)|CRITICALLY LOW", v):
        return "lo3"
    if re.search(r"↓↓|MARKEDLY (LOW|DECREASED)", v):
        return "lo2"
    if re.search(r"↓|LOW|DECREASED|BELOW REFERENCE", v):
        return "lo"
    if re.search(r"NORMAL|NEGATIVE|NO GROWTH|NO PATHOGEN|NO SIGNIFICANT|INTACT|PRESENT AND NORMAL", v):
        return "ok"
    return "neutral"


FLAG_STYLE = {
    "crit":    {"bg": "#FFF0F0", "text": "#8B0000", "badge": "CRITICAL",   "badgeBg": "#C03030", "badgeText": "#fff"},
    "hi2":     {"bg": "#FFF4EC", "text": "#8B3A00", "badge": "↑↑",         "badgeBg": "#C05020", "badgeText": "#fff"},
    "hi":      {"bg": "#FFFBF0", "text": "#7B4A00", "badge": "↑",          "badgeBg": "#B07020", "badgeText": "#fff"},
    "absent":  {"bg": "#F5F0FF", "text": "#4A1A7A", "badge": "ABSENT",     "badgeBg": "#7040B0", "badgeText": "#fff"},
    "diag":    {"bg": "#F0FFF4", "text": "#1A5E30", "badge": "DIAGNOSTIC",  "badgeBg": "#1D7A40", "badgeText": "#fff"},
    "lo3":     {"bg": "#EEF4FF", "text": "#1A3A8B", "badge": "↓↓↓",        "badgeBg": "#2050B0", "badgeText": "#fff"},
    "lo2":     {"bg": "#F0F5FF", "text": "#1A408B", "badge": "↓↓",         "badgeBg": "#2060B0", "badgeText": "#fff"},
    "lo":      {"bg": "#F2F6FF", "text": "#204890", "badge": "↓",          "badgeBg": "#3070C0", "badgeText": "#fff"},
    "ok":      {"bg": "#F5FFF8", "text": "#1A5030", "badge": None,         "badgeBg": None,      "badgeText": None},
    "neutral": {"bg": "transparent", "text": "#1A1714", "badge": None,     "badgeBg": None,      "badgeText": None},
}


def format_lab_result(test_name, result_text):
    return f"__LAB__{test_name}\n{result_text}"


TEST_ALIASES = [
    {"aliases": ["cbc", "full blood count", "fbc", "complete blood count", "blood count", "haemoglobin", "hemoglobin", "hb", "wbc", "white cell", "white blood", "neutrophil count", "eosinophil", "platelet", "lymphocyte count", "differential", "alc", "absolute lymphocyte"], "key": "CBC"},
    {"aliases": ["crp", "c reactive", "c-reactive", "inflammatory marker"], "key": "CRP"},
    {"aliases": ["esr", "erythrocyte sedimentation"], "key": "ESR"},
    {"aliases": ["procalcitonin", "pct"], "key": "procalcitonin"},
    {"aliases": ["biochemistry", "blood biochemistry", "lft", "liver function", "renal function", "urea", "creatinine", "electrolytes", "electrolyte", "u&e", "u and e", "kidney function", "egfr", "sodium", "potassium", "glucose", "alt", "ast", "bilirubin", "albumin", "total protein", "metabolic panel", "liver enzyme", "liver panel", "hepatic"], "key": "blood biochemistry"},
    {"aliases": ["immunoglobulin", "igg", "iga", "igm", "ige", "igd", "antibody level", "serum protein", "protein electrophoresis", "spep"], "key": "immunoglobulin"},
    {"aliases": ["complement", "c3", "c4", "ch50", "ch 50"], "key": "complement"},
    {"aliases": ["blood culture", "bacteraemia", "bacteremia", "sepsis screen", "bcx"], "key": "blood culture"},
    {"aliases": ["urinalysis", "urine", "urine dip", "dipstick", "urine mc&s", "urine culture", "mid stream", "mcsu", "mssu", "urine dipstick"], "key": "urinalysis"},
    {"aliases": ["throat swab", "throat culture", "throat pcr", "throat", "rapid strep", "strep test", "rapid antigen"], "key": "throat"},
    {"aliases": ["ear swab", "ear culture", "ear discharge", "aural swab"], "key": "ear swab"},
    {"aliases": ["skin swab", "wound swab", "wound culture", "abscess culture", "abscess swab", "skin culture", "lesion swab", "pus swab", "pus culture"], "key": "wound swab"},
    {"aliases": ["stool", "faeces", "feces", "stool culture", "stool pcr", "mtb pcr", "tuberculosis pcr", "bcg pcr", "gastric lavage", "giardia", "stool examination", "ova cyst"], "key": "stool"},
    {"aliases": ["sputum", "bal", "bronchoalveolar", "bronchoscopy", "sputum culture", "galactomannan", "aspergillus pcr"], "key": "sputum"},
    {"aliases": ["chest xray", "chest x-ray", "chest x ray", "cxr", "cxr chest", "chest film", "chest radiograph", "x ray chest", "xray chest", "plain film", "plain chest", "erect chest"], "key": "chest X-ray"},
    {"aliases": ["chest ct", "ct chest", "ct thorax", "hrct", "high resolution ct", "lung ct", "ct scan chest", "ct pulmonary"], "key": "chest CT"},
    {"aliases": ["abdominal ultrasound", "abdominal us", "abdominal scan", "abdo us", "abdo scan", "liver scan", "abdominal ct", "ct abdomen", "liver ultrasound", "renal ultrasound", "usg abdomen", "abdominal imaging"], "key": "abdominal"},
    {"aliases": ["spine xray", "spine x-ray", "scoliosis xray", "skeletal xray", "bone xray", "bone scan", "dexa", "bone density", "spinal xray"], "key": "spine"},
    {"aliases": ["dental xray", "opg", "orthopantomogram", "dental panoramic", "panoramic xray"], "key": "dental"},
    {"aliases": ["echo", "echocardiogram", "cardiac echo", "heart scan", "cardiac ultrasound", "ecg", "ekg", "electrocardiogram"], "key": "echocardiogram"},
    {"aliases": ["lymphocyte subset", "flow cytometry", "flow cytometry", "lymphocyte panel", "t cell", "b cell", "nk cell", "cd3", "cd4", "cd8", "cd19", "cd16", "cd56", "btk protein", "btk expression", "immunophenotyping", "facs"], "key": "lymphocyte subsets"},
    {"aliases": ["vaccine antibody", "vaccine titre", "vaccine titer", "pneumococcal antibody", "tetanus antibody", "hib antibody", "specific antibody", "functional antibody", "protective antibody"], "key": "vaccine antibody"},
    {"aliases": ["hiv", "retrovirus", "hiv test", "hiv serology"], "key": "HIV"},
    {"aliases": ["dhr", "dihydrorhodamine", "oxidative burst", "neutrophil function", "phagocyte function", "nbt", "nitroblue", "oxidative killing"], "key": "DHR"},
    {"aliases": ["trec", "t cell receptor excision", "newborn screening", "trec assay"], "key": "TREC"},
    {"aliases": ["chimerism", "qf-pcr", "maternal engraftment", "maternal t cell", "qfpcr", "chimerism testing"], "key": "chimerism"},
    {"aliases": ["gene panel", "genetic panel", "genetic testing", "exome", "wes", "whole exome", "ngs", "next generation", "immunodeficiency panel", "iei panel", "primary immunodeficiency panel", "gene sequencing", "genetic sequencing"], "key": "immunodeficiency gene panel"},
    {"aliases": ["autoinflammatory", "mefv", "fmf gene", "mediterranean fever gene", "traps gene", "tnfrsf1a", "mvk", "hids", "nlrp3", "caps", "autoinflammatory panel"], "key": "autoinflammatory"},
    {"aliases": ["cytokine", "il-17", "il17", "interleukin", "il-1", "il1", "interferon", "tnf", "cytokine panel"], "key": "cytokine"},
    {"aliases": ["monospot", "ebv serology", "ebv antibody", "glandular fever", "infectious mono", "mono test"], "key": "monospot"},
    {"aliases": ["ferritin", "iron studies", "iron level", "transferrin", "tsat"], "key": "ferritin"},
    {"aliases": ["skin biopsy", "biopsy", "punch biopsy", "histology", "histopathology"], "key": "skin biopsy"},
    {"aliases": ["lateral neck", "adenoid xray", "adenoid xray", "neck xray", "lateral neck xray"], "key": "lateral neck"},
    {"aliases": ["colonoscopy", "colonic biopsy", "bowel biopsy", "gi endoscopy", "endoscopy", "colonoscope"], "key": "colonoscopy"},
    {"aliases": ["hies score", "nih score", "nih hies", "job score"], "key": "NIH HIES"},
]


def detect_tests_in_message(text):
    lower = text.lower()
    found = []
    for entry in TEST_ALIASES:
        if any(alias in lower for alias in entry["aliases"]):
            found.append(entry["key"])
    return list(dict.fromkeys(found))


def is_test_order(text):
    lower = text.lower()
    order_words = ["order", "request", "would like", "i'd like", "i want", "can we", "let's", "let us", "please send", "please get", "please check", "send off", "check a", "get a", "run a", "do a", "do some", "take a", "arrange", "perform", "carry out", "i need", "we need", "please do", "can you get", "can you check", "can you order", "can you run", "could we", "could you get"]
    has_order_word = any(w in lower for w in order_words)
    tests = detect_tests_in_message(text)
    is_just_test_names = bool(re.match(r"^[\w\s,/+&\-\.()]+\Z", text)) and len(text) < 80 and len(tests) > 0
    return (has_order_word and len(tests) > 0) or is_just_test_names


def find_lab_result(case_lab_data, key_fragment):
    lower = key_fragment.lower()
    for k, v in case_lab_data.items():
        if lower in k.lower() or any(len(w) > 2 and w in k.lower() for w in lower.split(" ")):
            return (k, v)
    return None
