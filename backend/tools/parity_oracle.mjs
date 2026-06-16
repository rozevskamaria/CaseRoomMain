import { writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const FIXTURE_DIR = resolve(__dirname, "..", "tests", "fixtures", "parity");

const XLA = {
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
};

function parseLabText(text) {
  const raw = text
    .replace(/\. NOTE:/gi, "\nNOTE:")
    .replace(/\. ⚠/g, "\n⚠")
    .replace(/\. KEY:/gi, "\nKEY:")
    .split(/\.\s+(?=[A-Z])/)
    .map(s => s.trim().replace(/\.$/, "").trim())
    .filter(Boolean);

  return raw.map(sentence => {
    if (/^(NOTE|⚠|KEY|IMPORTANT|WARNING)[:!]/i.test(sentence)) {
      return { type: "note", text: sentence.replace(/^(NOTE|⚠|KEY|IMPORTANT|WARNING)[:!]\s*/i, "") };
    }
    const colonIdx = sentence.indexOf(":");
    if (colonIdx > 0 && colonIdx < 60) {
      return {
        type: "row",
        param: sentence.substring(0, colonIdx).trim(),
        value: sentence.substring(colonIdx + 1).trim(),
      };
    }
    const m = sentence.match(/^([A-Za-z][A-Za-z0-9+\-\/\s]{0,35}?)\s+([<>≤≥~]?[\d\.,]+.*)$/);
    if (m) {
      return { type: "row", param: m[1].trim(), value: m[2].trim() };
    }
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

const TEST_ALIASES = [
  { aliases: ["cbc","full blood count","fbc","complete blood count","blood count","haemoglobin","hemoglobin","hb","wbc","white cell","white blood","neutrophil count","eosinophil","platelet","lymphocyte count","differential","alc","absolute lymphocyte"], key: "CBC" },
  { aliases: ["crp","c reactive","c-reactive","inflammatory marker"], key: "CRP" },
  { aliases: ["esr","erythrocyte sedimentation"], key: "ESR" },
  { aliases: ["procalcitonin","pct"], key: "procalcitonin" },
  { aliases: ["biochemistry","blood biochemistry","lft","liver function","renal function","urea","creatinine","electrolytes","electrolyte","u&e","u and e","kidney function","egfr","sodium","potassium","glucose","alt","ast","bilirubin","albumin","total protein","metabolic panel","liver enzyme","liver panel","hepatic"], key: "blood biochemistry" },
  { aliases: ["immunoglobulin","igg","iga","igm","ige","igd","antibody level","serum protein","protein electrophoresis","spep"], key: "immunoglobulin" },
  { aliases: ["complement","c3","c4","ch50","ch 50"], key: "complement" },
  { aliases: ["blood culture","bacteraemia","bacteremia","sepsis screen","bcx"], key: "blood culture" },
  { aliases: ["urinalysis","urine","urine dip","dipstick","urine mc&s","urine culture","mid stream","mcsu","mssu","urine dipstick"], key: "urinalysis" },
  { aliases: ["throat swab","throat culture","throat pcr","throat","rapid strep","strep test","rapid antigen"], key: "throat" },
  { aliases: ["ear swab","ear culture","ear discharge","aural swab"], key: "ear swab" },
  { aliases: ["skin swab","wound swab","wound culture","abscess culture","abscess swab","skin culture","lesion swab","pus swab","pus culture"], key: "wound swab" },
  { aliases: ["stool","faeces","feces","stool culture","stool pcr","mtb pcr","tuberculosis pcr","bcg pcr","gastric lavage","giardia","stool examination","ova cyst"], key: "stool" },
  { aliases: ["sputum","bal","bronchoalveolar","bronchoscopy","sputum culture","galactomannan","aspergillus pcr"], key: "sputum" },
  { aliases: ["chest xray","chest x-ray","chest x ray","cxr","cxr chest","chest film","chest radiograph","x ray chest","xray chest","plain film","plain chest","erect chest"], key: "chest X-ray" },
  { aliases: ["chest ct","ct chest","ct thorax","hrct","high resolution ct","lung ct","ct scan chest","ct pulmonary"], key: "chest CT" },
  { aliases: ["abdominal ultrasound","abdominal us","abdominal scan","abdo us","abdo scan","liver scan","abdominal ct","ct abdomen","liver ultrasound","renal ultrasound","usg abdomen","abdominal imaging"], key: "abdominal" },
  { aliases: ["spine xray","spine x-ray","scoliosis xray","skeletal xray","bone xray","bone scan","dexa","bone density","spinal xray"], key: "spine" },
  { aliases: ["dental xray","opg","orthopantomogram","dental panoramic","panoramic xray"], key: "dental" },
  { aliases: ["echo","echocardiogram","cardiac echo","heart scan","cardiac ultrasound","ecg","ekg","electrocardiogram"], key: "echocardiogram" },
  { aliases: ["lymphocyte subset","flow cytometry","flow cytometry","lymphocyte panel","t cell","b cell","nk cell","cd3","cd4","cd8","cd19","cd16","cd56","btk protein","btk expression","immunophenotyping","facs"], key: "lymphocyte subsets" },
  { aliases: ["vaccine antibody","vaccine titre","vaccine titer","pneumococcal antibody","tetanus antibody","hib antibody","specific antibody","functional antibody","protective antibody"], key: "vaccine antibody" },
  { aliases: ["hiv","retrovirus","hiv test","hiv serology"], key: "HIV" },
  { aliases: ["dhr","dihydrorhodamine","oxidative burst","neutrophil function","phagocyte function","nbt","nitroblue","oxidative killing"], key: "DHR" },
  { aliases: ["trec","t cell receptor excision","newborn screening","trec assay"], key: "TREC" },
  { aliases: ["chimerism","qf-pcr","maternal engraftment","maternal t cell","qfpcr","chimerism testing"], key: "chimerism" },
  { aliases: ["gene panel","genetic panel","genetic testing","exome","wes","whole exome","ngs","next generation","immunodeficiency panel","iei panel","primary immunodeficiency panel","gene sequencing","genetic sequencing"], key: "immunodeficiency gene panel" },
  { aliases: ["autoinflammatory","mefv","fmf gene","mediterranean fever gene","traps gene","tnfrsf1a","mvk","hids","nlrp3","caps","autoinflammatory panel"], key: "autoinflammatory" },
  { aliases: ["cytokine","il-17","il17","interleukin","il-1","il1","interferon","tnf","cytokine panel"], key: "cytokine" },
  { aliases: ["monospot","ebv serology","ebv antibody","glandular fever","infectious mono","mono test"], key: "monospot" },
  { aliases: ["ferritin","iron studies","iron level","transferrin","tsat"], key: "ferritin" },
  { aliases: ["skin biopsy","biopsy","punch biopsy","histology","histopathology"], key: "skin biopsy" },
  { aliases: ["lateral neck","adenoid xray","adenoid xray","neck xray","lateral neck xray"], key: "lateral neck" },
  { aliases: ["colonoscopy","colonic biopsy","bowel biopsy","gi endoscopy","endoscopy","colonoscope"], key: "colonoscopy" },
  { aliases: ["hies score","nih score","nih hies","job score"], key: "NIH HIES" },
];

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

function isTestOrder(text) {
  const lower = text.toLowerCase();
  const orderWords = ["order","request","would like","i'd like","i want","can we","let's","let us","please send","please get","please check","send off","check a","get a","run a","do a","do some","take a","arrange","perform","carry out","i need","we need","please do","can you get","can you check","can you order","can you run","could we","could you get"];
  const hasOrderWord = orderWords.some(w => lower.includes(w));
  const tests = detectTestsInMessage(text);
  const isJustTestNames = /^[\w\s,/+&\-\.()]+$/.test(text) && text.length < 80 && tests.length > 0;
  return (hasOrderWord && tests.length > 0) || isJustTestNames;
}

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

const TUTOR_EVAL_SUFFIX = {
  summary: "Evaluate this clinical summary from a medical student (3–4 sentences, encouraging, identify what's good and what's missing).",
  differential: "Evaluate these differentials from a medical student. Be encouraging, guide without giving away the answer. 3–5 sentences.",
  interpretation: "Evaluate this test interpretation from a medical student. Highlight what is correct and gently redirect any errors. End with a brief question that nudges them toward the next step. 3–5 sentences. Warm and constructive.",
};

const REFLECTION_QS = [
  "What was your initial diagnosis when you first heard the case opening?",
  "Which specific finding or test result changed your thinking most significantly?",
  "Was there a moment where you felt uncertain or stuck? What helped you move forward?",
  "What would you do differently if you encountered this case again?",
  "What is the single most important clinical or scientific concept you will take away from this case?",
];

const makeReflectionSummaryPrompt = (c) => `You are summarising a medical student's reflection on a clinical case: "${c.title}" (target diagnosis: ${c.targetDiagnosis}). Write 3–4 supportive sentences summarising their reflective reasoning and identifying 1–2 key learning moments. Encourage continued reflection.`;

function buildHintContext({ title, targetDiagnosis, phase, parentExchanges, studentQuestions, orderedList, labDataKeys, keyClues, hintsUsed }) {
  const notYetOrdered = labDataKeys.filter(k => !orderedList.some(o => k.toLowerCase().includes(o.toLowerCase()) || o.toLowerCase().includes(k.toLowerCase())));
  const importantMissing = keyClues.filter(clue => {
    const clueWords = clue.toLowerCase().split(" ").filter(w => w.length > 4);
    return !studentQuestions.toLowerCase().includes(clueWords[0]) && !orderedList.some(t => clueWords.some(w => t.toLowerCase().includes(w)));
  });

  const context = `
CASE: ${title}
TARGET DIAGNOSIS: ${targetDiagnosis}
CURRENT PHASE: ${phase}
PARENT EXCHANGES SO FAR: ${parentExchanges}
STUDENT HAS ASKED ABOUT: ${studentQuestions || "nothing yet"}
TESTS ORDERED SO FAR: ${orderedList.length > 0 ? orderedList.join(", ") : "none"}
TESTS NOT YET ORDERED (available in this case): ${notYetOrdered.slice(0, 8).join(", ")}
KEY CLUES NOT YET FOUND: ${importantMissing.slice(0, 3).join("; ")}
HINTS USED SO FAR: ${hintsUsed}
    `.trim();

  return { notYetOrdered, importantMissing, context };
}

const parseLabTextInputs = [];
for (const [k, v] of Object.entries(XLA.labData)) {
  parseLabTextInputs.push(v);
}
parseLabTextInputs.push("CRP 84 mg/L. NOTE: this is elevated");
parseLabTextInputs.push("WBC normal. ⚠ critical value flagged");
parseLabTextInputs.push("IgG very low. KEY: hallmark finding");
parseLabTextInputs.push("IMPORTANT! escalate now");
parseLabTextInputs.push("WARNING: contamination possible");
parseLabTextInputs.push("This is a very long descriptive parameter name that exceeds the sixty character colon threshold: value here");
parseLabTextInputs.push("Just a plain sentence with no match at all");
parseLabTextInputs.push("");
parseLabTextInputs.push("WBC 6,200/µL (normal). Neutrophils 4,500/µL (normal)");

const parseLabTextFixtures = parseLabTextInputs.map(input => ({ input, output: parseLabText(input) }));

const flagRowInputSet = new Set();
for (const v of Object.values(XLA.labData)) {
  for (const row of parseLabText(v)) {
    if (row.type === "row") flagRowInputSet.add(row.value);
  }
}
const flagRowExtraInputs = [
  "Procalcitonin 2.8 ng/mL ↑↑ (elevated)",
  "CRITICALLY elevated marker",
  "MARKEDLY ELEVATED enzyme",
  "ELEVATED CRP",
  "HIGH count",
  "POSITIVE for Streptococcus",
  "POSITIVE (bacteraemia confirmed)",
  "RAISED inflammatory marker",
  "ABSENT B cells",
  "UNDETECTABLE IgA",
  "B cells 0.0%",
  "VIRTUALLY ABSENT response",
  "DIAGNOSTIC pattern",
  "PATHOGNOMONIC finding",
  "↓↓↓ severely decreased",
  "SEVERELY LOW count",
  "SEVERELY DECREASED level",
  "CRITICALLY LOW value",
  "MARKEDLY LOW value",
  "MARKEDLY DECREASED value",
  "LOW for age",
  "DECREASED level",
  "BELOW REFERENCE range",
  "NORMAL result",
  "NEGATIVE serology",
  "NO GROWTH on culture",
  "NO PATHOGEN isolated",
  "NO SIGNIFICANT growth",
  "INTACT response",
  "PRESENT AND NORMAL architecture",
  "something completely unremarkable text",
];
for (const x of flagRowExtraInputs) flagRowInputSet.add(x);
const flagRowFixtures = [...flagRowInputSet].map(input => ({ input, output: flagRow(input) }));

const detectInputs = [
  "I would like to order a full blood count",
  "Please send bloods for CRP and ESR",
  "Can we get immunoglobulins please",
  "I'd like to request a chest x-ray",
  "Let's do a lymphocyte subset panel",
  "order blood culture",
  "cbc",
  "crp",
  "esr",
  "immunoglobulins igg iga igm",
  "flow cytometry",
  "lymphocyte subsets, flow cytometry",
  "adenoid xray",
  "lateral neck xray",
  "throat swab and ear swab",
  "echo",
  "ecg",
  "hiv test",
  "gene panel",
  "DHR oxidative burst",
  "How long has he been unwell?",
  "What infections has he had?",
  "Tell me about the family history",
  "cbc, crp, esr, immunoglobulins, complement, hiv test, gene panel",
  "abdo us",
  "ct chest",
  "biopsy",
  "stool for giardia",
  "I want to perform a skin prick test",
  "we need to arrange an echocardiogram",
  "Please order a CBC, CRP, ESR, immunoglobulins, complement, lymphocyte subsets, blood culture too",
  "nothing relevant here",
];
const detectTestsFixtures = detectInputs.map(input => ({ input, output: detectTestsInMessage(input) }));
const isTestOrderFixtures = detectInputs.map(input => ({ input, output: isTestOrder(input) }));

const findLabInputs = [
  "immunoglobulin",
  "throat",
  "cbc",
  "CBC",
  "complement",
  "chest x-ray",
  "chest CT",
  "abdominal",
  "lymphocyte subsets",
  "vaccine antibody",
  "stool",
  "HIV",
  "ferritin",
  "gene panel",
  "ecg",
  "ear",
  "urine",
  "blood culture",
  "procalcitonin",
  "a nonexistent test fragment",
];
const findLabResultFixtures = findLabInputs.map(input => ({ input, output: findLabResult(XLA.labData, input) }));

const tutorPhases = ["history", "summary", "examination", "differential", "tests", "interpretation"];
const tutorModes = ["practice", "exam"];
const makeTutorPromptFixtures = [];
for (const phase of tutorPhases) {
  for (const mode of tutorModes) {
    makeTutorPromptFixtures.push({
      input: { case: XLA.id, phase, mode },
      output: makeTutorPrompt(XLA, phase, mode),
    });
  }
}

const tutorEvalSuffixFixtures = Object.entries(TUTOR_EVAL_SUFFIX).map(([phase, suffix]) => ({
  input: { phase },
  output: suffix,
}));

const composedTutorEvalFixtures = [];
for (const phase of ["summary", "differential", "interpretation"]) {
  for (const mode of tutorModes) {
    composedTutorEvalFixtures.push({
      input: { case: XLA.id, phase, mode },
      output: `${makeTutorPrompt(XLA, phase, mode)}\n\n${TUTOR_EVAL_SUFFIX[phase]}`,
    });
  }
}

const makeFeedbackPromptFixtures = [
  { input: { case: XLA.id }, output: makeFeedbackPrompt(XLA) },
];

const hintStates = [
  {
    title: XLA.title,
    targetDiagnosis: XLA.targetDiagnosis,
    phase: "history",
    parentExchanges: 0,
    studentQuestions: "",
    orderedList: [],
    labDataKeys: Object.keys(XLA.labData),
    keyClues: XLA.keyClues,
    hintsUsed: 1,
  },
  {
    title: XLA.title,
    targetDiagnosis: XLA.targetDiagnosis,
    phase: "tests",
    parentExchanges: 4,
    studentQuestions: "How long has he been unwell? | Any family history of infections?",
    orderedList: ["CBC", "CRP", "ESR"],
    labDataKeys: Object.keys(XLA.labData),
    keyClues: XLA.keyClues,
    hintsUsed: 2,
  },
  {
    title: XLA.title,
    targetDiagnosis: XLA.targetDiagnosis,
    phase: "differential",
    parentExchanges: 7,
    studentQuestions: "Tell me about the tonsils | What about the maternal uncle who died?",
    orderedList: ["immunoglobulins", "lymphocyte subsets / flow cytometry", "complement / C3 C4", "chest X-ray", "blood culture", "CBC / full blood count", "CRP", "ESR", "HIV test"],
    labDataKeys: Object.keys(XLA.labData),
    keyClues: XLA.keyClues,
    hintsUsed: 3,
  },
];
const buildHintContextFixtures = hintStates.map(input => ({ input, output: buildHintContext(input) }));

const reflectionFixtures = [
  { input: { kind: "REFLECTION_QS" }, output: REFLECTION_QS },
  { input: { kind: "reflectionSummaryPrompt", case: XLA.id }, output: makeReflectionSummaryPrompt(XLA) },
];

const FIXTURES = {
  parseLabText: parseLabTextFixtures,
  flagRow: flagRowFixtures,
  detectTestsInMessage: detectTestsFixtures,
  isTestOrder: isTestOrderFixtures,
  findLabResult: findLabResultFixtures,
  makeTutorPrompt: makeTutorPromptFixtures,
  tutorEvalSuffix: tutorEvalSuffixFixtures,
  composedTutorEval: composedTutorEvalFixtures,
  makeFeedbackPrompt: makeFeedbackPromptFixtures,
  buildHintContext: buildHintContextFixtures,
  reflection: reflectionFixtures,
};

mkdirSync(FIXTURE_DIR, { recursive: true });

const written = [];
for (const [name, data] of Object.entries(FIXTURES)) {
  const path = resolve(FIXTURE_DIR, `${name}.json`);
  writeFileSync(path, JSON.stringify(data, null, 2) + "\n");
  written.push({ name, path, count: data.length });
}

for (const w of written) {
  process.stdout.write(`${w.name}\t${w.count}\t${w.path}\n`);
}
process.stdout.write(`TOTAL_FILES\t${written.length}\n`);
