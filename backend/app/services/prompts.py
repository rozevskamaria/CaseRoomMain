from app.schemas.case import Case

LANGUAGE_DIRECTIVE_LV = (
    "LANGUAGE: Respond entirely in Latvian (latviešu valodā). All prose you "
    "generate must be in Latvian."
)


def language_directive(language: str) -> str:
    if language == "lv":
        return LANGUAGE_DIRECTIVE_LV
    return ""


def _with_directive(prompt: str, language: str) -> str:
    directive = language_directive(language)
    if not directive:
        return prompt
    return f"{prompt}\n\n{directive}"


def make_tutor_prompt(
    case: Case, phase: str, mode: str, language: str = "en"
) -> str:
    wrong_path_guidance = "\n".join(
        f'- If student says "{k}": {v}' for k, v in case.wrong_paths.items()
    )
    key_clues = "; ".join(case.key_clues)
    base = f"""You are the CLINICAL TUTOR in a medical student training simulation for Inborn Errors of Immunity.

Current case: "{case.title}" — Target diagnosis: {case.target_diagnosis}
Current phase: {phase}
Mode: {mode}

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
{wrong_path_guidance}

KEY CLUES they should find: {key_clues}"""
    return _with_directive(base, language)


def make_feedback_prompt(case: Case, language: str = "en") -> str:
    key_clues = "; ".join(case.key_clues)
    base = f"""You are generating STRUCTURED FORMATIVE FEEDBACK for a clinical immunology case simulation.

Case: "{case.title}"
Target diagnosis: {case.target_diagnosis}
IUIS category: {case.target_iuis}
Key clues: {key_clues}
Model management: {case.model_management}
Model genetic counselling: {case.model_genetic_counselling}

Generate feedback in this EXACT JSON structure (no markdown, pure JSON):
{{
  "diagnosticAccuracy": "correct|partially_correct|incorrect",
  "diagnosticComment": "1-2 sentences on diagnosis accuracy",
  "wellDone": ["point1", "point2", "point3"],
  "missing": ["point1", "point2"],
  "keyClues": ["clue1", "clue2", "clue3"],
  "reasoningPathway": "3-4 sentence ideal reasoning pathway",
  "managementPoints": ["point1", "point2", "point3"],
  "geneticPoints": ["point1", "point2"],
  "revisionTopic": "1-2 sentence suggested revision topic",
  "scores": {{
    "historyTaking": "Excellent|Good|Developing|Needs review",
    "examination": "Excellent|Good|Developing|Needs review",
    "differential": "Excellent|Good|Developing|Needs review",
    "testSelection": "Excellent|Good|Developing|Needs review",
    "interpretation": "Excellent|Good|Developing|Needs review",
    "management": "Excellent|Good|Developing|Needs review"
  }}
}}"""
    directive = language_directive(language)
    if not directive:
        return base
    return (
        f"{base}\n\n{directive}\n"
        "Write all free-text VALUES in Latvian. Keep every JSON key exactly as "
        'shown in English. "diagnosticAccuracy" must remain one of '
        "correct|partially_correct|incorrect and every value under "
        '"scores" must remain one of Excellent|Good|Developing|Needs review.'
    )


SCORE_ENUM = ["Excellent", "Good", "Developing", "Needs review"]

FEEDBACK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "diagnosticAccuracy": {
            "type": "string",
            "enum": ["correct", "partially_correct", "incorrect"],
        },
        "diagnosticComment": {"type": "string"},
        "wellDone": {"type": "array", "items": {"type": "string"}},
        "missing": {"type": "array", "items": {"type": "string"}},
        "keyClues": {"type": "array", "items": {"type": "string"}},
        "reasoningPathway": {"type": "string"},
        "managementPoints": {"type": "array", "items": {"type": "string"}},
        "geneticPoints": {"type": "array", "items": {"type": "string"}},
        "revisionTopic": {"type": "string"},
        "scores": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "historyTaking": {"type": "string", "enum": SCORE_ENUM},
                "examination": {"type": "string", "enum": SCORE_ENUM},
                "differential": {"type": "string", "enum": SCORE_ENUM},
                "testSelection": {"type": "string", "enum": SCORE_ENUM},
                "interpretation": {"type": "string", "enum": SCORE_ENUM},
                "management": {"type": "string", "enum": SCORE_ENUM},
            },
            "required": [
                "historyTaking",
                "examination",
                "differential",
                "testSelection",
                "interpretation",
                "management",
            ],
        },
    },
    "required": [
        "diagnosticAccuracy",
        "diagnosticComment",
        "wellDone",
        "missing",
        "keyClues",
        "reasoningPathway",
        "managementPoints",
        "geneticPoints",
        "revisionTopic",
        "scores",
    ],
}


SUMMARY_EVAL_SUFFIX = "Evaluate this clinical summary from a medical student (3–4 sentences, encouraging, identify what's good and what's missing)."

DIFFERENTIAL_EVAL_SUFFIX = "Evaluate these differentials from a medical student. Be encouraging, guide without giving away the answer. 3–5 sentences."

INTERPRETATION_EVAL_SUFFIX = "Evaluate this test interpretation from a medical student. Highlight what is correct and gently redirect any errors. End with a brief question that nudges them toward the next step. 3–5 sentences. Warm and constructive."


def make_summary_eval_prompt(case: Case, mode: str, language: str = "en") -> str:
    base = make_tutor_prompt(case, "summary", mode)
    return _with_directive(f"{base}\n\n{SUMMARY_EVAL_SUFFIX}", language)


def make_differential_eval_prompt(
    case: Case, mode: str, language: str = "en"
) -> str:
    base = make_tutor_prompt(case, "differential", mode)
    return _with_directive(f"{base}\n\n{DIFFERENTIAL_EVAL_SUFFIX}", language)


def make_interpretation_eval_prompt(
    case: Case, mode: str, language: str = "en"
) -> str:
    base = make_tutor_prompt(case, "interpretation", mode)
    return _with_directive(f"{base}\n\n{INTERPRETATION_EVAL_SUFFIX}", language)


def build_hint_context(
    case: Case,
    phase: str,
    msgs: list[dict],
    ordered_tests: list[str],
    hints_used: int,
) -> dict:
    parent_exchange = len([m for m in msgs if m.get("type") == "parent"])
    student_questions = " | ".join(
        m.get("text", "") for m in msgs if m.get("type") == "student"
    )
    ordered_list = list(ordered_tests)
    not_yet_ordered = [
        k
        for k in case.lab_data.keys()
        if not any(
            k.lower() in o.lower() or o.lower() in k.lower() for o in ordered_list
        )
    ]
    important_missing = []
    for clue in case.key_clues:
        clue_words = [w for w in clue.lower().split(" ") if len(w) > 4]
        first_word = clue_words[0] if clue_words else "undefined"
        in_questions = first_word in student_questions.lower()
        in_ordered = any(
            any(w in t.lower() for w in clue_words) for t in ordered_list
        )
        if not in_questions and not in_ordered:
            important_missing.append(clue)

    tests_ordered = ", ".join(ordered_list) if len(ordered_list) > 0 else "none"
    context = f"""
CASE: {case.title}
TARGET DIAGNOSIS: {case.target_diagnosis}
CURRENT PHASE: {phase}
PARENT EXCHANGES SO FAR: {parent_exchange}
STUDENT HAS ASKED ABOUT: {student_questions or "nothing yet"}
TESTS ORDERED SO FAR: {tests_ordered}
TESTS NOT YET ORDERED (available in this case): {", ".join(not_yet_ordered[0:8])}
KEY CLUES NOT YET FOUND: {"; ".join(important_missing[0:3])}
HINTS USED SO FAR: {hints_used}
    """.strip()
    return {
        "notYetOrdered": not_yet_ordered,
        "importantMissing": important_missing,
        "context": context,
    }


def build_hint_system_prompt(context: str, language: str = "en") -> str:
    base = f"""You are a supportive clinical tutor giving a CONTEXTUAL HINT to a medical student who is stuck.

{context}

HINT RULES:
- Give ONE specific, actionable hint based on what the student has NOT yet done
- Do NOT reveal the diagnosis directly
- Do NOT say "the diagnosis is..."
- Scale specificity to hints used: first hint = broad direction; second = specific gap; third = name the single most important missing test or history point
- If no tests have been ordered yet → suggest a test CATEGORY (not a specific name) that would help, e.g. "What basic blood tests would you order for any child with recurrent infections?"
- If some tests ordered but key ones missing → hint toward the gap, e.g. "You have checked the basic bloods — what does the immunology tell you about specific immune compartments?"
- If tests done but history thin → point to the missing history element
- If in differential phase → ask a Socratic question that narrows the field
- Keep the hint to 2–4 sentences. Warm, encouraging tone. Never say "wrong.\""""
    return _with_directive(base, language)


HINT_FALLBACK = "Think about which immune compartment is most likely affected given the type of infections. Then consider which basic blood tests would characterise that compartment."

HINT_FALLBACK_LV = "Padomājiet, kura imūnsistēmas daļa, visticamāk, ir skarta, ņemot vērā infekciju veidu. Tad apsveriet, kuras pamata asins analīzes raksturotu šo daļu."


def hint_fallback(language: str) -> str:
    if language == "lv":
        return HINT_FALLBACK_LV
    return HINT_FALLBACK


REFLECTION_QS = [
    "What was your initial diagnosis when you first heard the case opening?",
    "Which specific finding or test result changed your thinking most significantly?",
    "Was there a moment where you felt uncertain or stuck? What helped you move forward?",
    "What would you do differently if you encountered this case again?",
    "What is the single most important clinical or scientific concept you will take away from this case?",
]


def build_reflection_summary_prompt(case: Case, language: str = "en") -> str:
    base = f'You are summarising a medical student\'s reflection on a clinical case: "{case.title}" (target diagnosis: {case.target_diagnosis}). Write 3–4 supportive sentences summarising their reflective reasoning and identifying 1–2 key learning moments. Encourage continued reflection.'
    return _with_directive(base, language)
