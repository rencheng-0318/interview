from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from conditions import CONDITIONS, CONDITIONS_BY_KEY, Condition

SEED = 20260728
ANCHOR_DATE = date(2026, 7, 1)
DOCUMENT_HISTORY_DAYS = 1095
TOTAL_DOCUMENT_TARGET = 2400

DOCUMENT_TYPES = (
    "diagnostic_note",
    "specialist_note",
    "radiology_report",
    "lab_report",
)


@dataclass(frozen=True)
class PracticeSpec:
    id: str
    name: str
    slug: str
    city: str
    region: str
    document_budget: int
    is_primary: bool


PRACTICE_SPECS: tuple[PracticeSpec, ...] = (
    PracticeSpec(
        id="practice-northside",
        name="Northside Family Medicine",
        slug="northside",
        city="Northside",
        region="Riverton",
        document_budget=1200,
        is_primary=True,
    ),
    PracticeSpec(
        id="practice-lakeshore",
        name="Lakeshore Internal Medicine",
        slug="lakeshore",
        city="Lakeshore",
        region="Riverton",
        document_budget=700,
        is_primary=False,
    ),
    PracticeSpec(
        id="practice-summit",
        name="Summit Specialty Care",
        slug="summit",
        city="Summit",
        region="Halvard",
        document_budget=500,
        is_primary=False,
    ),
)

PRIMARY_PRACTICE = next(spec for spec in PRACTICE_SPECS if spec.is_primary)

FIRST_NAMES = (
    "Jordan",
    "Amara",
    "Priya",
    "Nikolai",
    "Rosa",
    "Devon",
    "Yusuf",
    "Clara",
    "Tobias",
    "Ines",
    "Malik",
    "Freya",
    "Hiro",
    "Naomi",
    "Elias",
    "Sunita",
    "Marcus",
    "Leila",
    "Anders",
    "Chidi",
    "Mei",
    "Rafael",
    "Bettina",
    "Omar",
    "Saoirse",
    "Kwame",
    "Iris",
    "Lucian",
    "Thandi",
    "Viktor",
    "Alina",
    "Emeka",
    "Noor",
    "Bram",
    "Carys",
    "Dmitri",
    "Esme",
    "Farid",
    "Greta",
    "Hanif",
    "Ilse",
    "Jonas",
    "Kira",
    "Lars",
    "Marisol",
    "Nadia",
    "Otto",
    "Pilar",
    "Quentin",
    "Rhian",
    "Soren",
    "Tamsin",
    "Ulrich",
    "Vera",
)

LAST_NAMES = (
    "Lee",
    "Okonkwo",
    "Vasquez",
    "Petrov",
    "Almeida",
    "Fitzgerald",
    "Haddad",
    "Nowak",
    "Brennan",
    "Costa",
    "Rahman",
    "Lindqvist",
    "Tanaka",
    "Mbeki",
    "Sorensen",
    "Kaur",
    "Delacroix",
    "Farrow",
    "Ibrahim",
    "Novotny",
    "Chen",
    "Moreau",
    "Kovac",
    "Adeyemi",
    "Rossi",
    "Halvorsen",
    "Bergstrom",
    "Nakamura",
    "Oyelaran",
    "Duarte",
    "Weiss",
    "Sandoval",
    "Kirwan",
    "Ferreira",
    "Yildiz",
    "Marchetti",
    "Osei",
    "Lindgren",
    "Pereira",
    "Schneider",
    "Aguirre",
    "Botha",
    "Cavanagh",
    "Dziedzic",
    "Eriksen",
)

CLINICIAN_NAMES = (
    "Dr M. Aldridge",
    "Dr S. Nakagawa",
    "Dr P. Oyelaran",
    "Dr L. Marchetti",
    "Dr R. Fitzgerald",
    "Dr H. Bergstrom",
    "Dr T. Okonkwo",
    "Dr A. Petrov",
    "Dr J. Delacroix",
    "Dr K. Rahman",
    "Dr E. Sandoval",
    "Dr N. Lindqvist",
)

STAFF_TEMPLATE = (
    ("clinician", "Dr Alex Reyes"),
    ("nurse", "Sam Whitfield"),
    ("admin", "Robin Achebe"),
)

DURATIONS = (
    "three weeks",
    "two months",
    "six weeks",
    "four days",
    "the past year",
    "eighteen months",
    "ten days",
    "several months",
    "five weeks",
    "nine months",
    "a fortnight",
    "the past two years",
)

ONSET_PHRASES = (
    "Symptoms began insidiously and have progressed since.",
    "Onset was abrupt and the pattern has been stable since.",
    "The pattern has been intermittent with a gradual increase in frequency.",
    "Symptoms fluctuate but have not fully resolved between episodes.",
    "There was a clear precipitant at onset, with partial recovery afterwards.",
    "The course has been relapsing, with two distinct flares so far.",
)

FUNCTIONAL_IMPACTS = (
    "Now avoids the stairs at home and rests on the landing.",
    "Has halved their usual weekly walking distance.",
    "Reports missing four days of work in the last month.",
    "No longer manages the weekly supermarket trip unaided.",
    "Has stopped attending a regular exercise class.",
    "Sleep is broken two to three times most nights.",
    "Struggles to carry shopping more than a short distance.",
    "Has given up gardening, which they previously did daily.",
    "Finds concentration at work noticeably harder.",
    "Declines social invitations because of the symptoms.",
    "Relies on family for transport to appointments.",
    "Continues to work full time but with reduced duties.",
)

SOCIAL_CONTEXTS = (
    "Works night shifts in a distribution centre.",
    "Recently retired after thirty years of teaching.",
    "Lives alone in a first-floor flat without a lift.",
    "Full-time carer for a relative with dementia.",
    "Self-employed and reluctant to take time off.",
    "Non-smoker, minimal alcohol, no recreational drug use.",
    "Ex-smoker with a twenty pack-year history, stopped four years ago.",
    "Lives with a partner and two school-age children.",
    "Recently relocated and registered with the practice this year.",
    "Works in construction with regular heavy lifting.",
    "Office-based role with a long daily commute.",
    "Currently between jobs and reports financial strain.",
)

ADHERENCE_NOTES = (
    "Adherence to previous therapy has been good.",
    "Reports intermittently missing evening doses.",
    "Has not tolerated a previous trial of first-line therapy.",
    "No previous treatment attempted for this problem.",
    "Prefers to avoid regular medication if possible.",
    "Has used over-the-counter remedies without benefit.",
    "Previous course was stopped early due to side effects.",
    "Willing to trial a preventative approach.",
)

FOLLOW_UP_NOTES = (
    "Review arranged in four weeks with the same clinician.",
    "Telephone follow-up booked for next week.",
    "Patient given written information and safety-netting advice.",
    "Will be reviewed after the requested investigations return.",
    "Advised to attend sooner if symptoms escalate.",
    "Added to the nurse-led monitoring list.",
    "Shared decision made to reassess in three months.",
    "Discharged back to the referring clinician with a plan.",
)


@dataclass(frozen=True)
class CuratedCase:
    id: str
    query: str
    condition_key: str
    decoy_practice_id: str
    distractor_condition_keys: tuple[str, ...]


CURATED_CASES: tuple[CuratedCase, ...] = (
    CuratedCase(
        id="case-migraine-aura",
        query="recurring headaches preceded by flashing lights, nausea, and sensitivity to light",
        condition_key="migraine_with_aura",
        decoy_practice_id="practice-lakeshore",
        distractor_condition_keys=("tension_headache", "cluster_headache"),
    ),
    CuratedCase(
        id="case-osmotic-symptoms",
        query="persistent thirst, frequent urination, and elevated glucose",
        condition_key="type2_diabetes",
        decoy_practice_id="practice-summit",
        distractor_condition_keys=("diabetes_insipidus", "chronic_kidney_disease"),
    ),
    CuratedCase(
        id="case-congestive-dyspnoea",
        query="shortness of breath with bilateral leg swelling",
        condition_key="heart_failure",
        decoy_practice_id="practice-lakeshore",
        distractor_condition_keys=("copd", "atrial_fibrillation"),
    ),
    CuratedCase(
        id="case-exertional-wheeze",
        query="exercise-related chest tightness and wheezing",
        condition_key="exercise_induced_asthma",
        decoy_practice_id="practice-summit",
        distractor_condition_keys=("copd", "allergic_rhinitis"),
    ),
    CuratedCase(
        id="case-nocturnal-foot-pain",
        query="burning pain in the feet at night with numbness",
        condition_key="diabetic_peripheral_neuropathy",
        decoy_practice_id="practice-lakeshore",
        distractor_condition_keys=("lumbar_radiculopathy", "osteoarthritis_knee"),
    ),
    CuratedCase(
        id="case-biliary-jaundice",
        query="yellowing of the eyes with pain in the upper right abdomen",
        condition_key="cholelithiasis",
        decoy_practice_id="practice-summit",
        distractor_condition_keys=("gerd", "urinary_tract_infection"),
    ),
)

CURATED_CONDITION_KEYS = frozenset(case.condition_key for case in CURATED_CASES)

RESERVED_CONDITION_KEYS = CURATED_CONDITION_KEYS | {
    key for case in CURATED_CASES for key in case.distractor_condition_keys
}
FILLER_CONDITIONS = tuple(c for c in CONDITIONS if c.key not in RESERVED_CONDITION_KEYS)
FILLER_CONDITION_KEYS = frozenset(c.key for c in FILLER_CONDITIONS)

QUERY_STOPWORDS = frozenset(
    "a an and the with of in on at to for by from is are was were be been my i we then "
    "that this it its as or but if into over under out up down about".split()
)


def content_words(text: str) -> frozenset[str]:
    return frozenset(
        word
        for word in re.findall(r"[a-z]+", text.lower())
        if word not in QUERY_STOPWORDS
    )


def filler_distractor_keys(condition: Condition) -> tuple[str, ...]:
    return tuple(
        key for key in condition.distractor_keys if key in FILLER_CONDITION_KEYS
    )


def content_bigrams(text: str) -> frozenset[tuple[str, str]]:
    words = [w for w in re.findall(r"[a-z]+", text.lower()) if w not in QUERY_STOPWORDS]
    return frozenset(zip(words, words[1:]))


def select_patient_quotes(query: str, lay_symptoms: tuple[str, ...]) -> list[str]:
    query_words = content_words(query)
    query_bigrams = content_bigrams(query)
    scored = sorted(
        (
            (len(query_words & content_words(s)) / max(len(query_words), 1), s)
            for s in lay_symptoms
        ),
        key=lambda pair: pair[0],
    )
    acceptable = [
        text
        for overlap, text in scored
        if overlap <= 0.5 and not (query_bigrams & content_bigrams(text))
    ]
    return acceptable or [scored[0][1]]


@dataclass
class Patient:
    id: str
    practice_id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str

    @property
    def age(self) -> int:
        return (ANCHOR_DATE - self.date_of_birth).days // 365


@dataclass
class Document:
    id: str
    practice_id: str
    patient_id: str
    document_type: str
    title: str
    document_date: date
    author_name: str
    body: str


@dataclass(frozen=True)
class RenderContext:
    condition: Condition
    voice: str
    age: int
    sex: str


class Sequence:
    def __init__(self, template: str) -> None:
        self._template = template
        self._next = 1

    def take(self) -> str:
        value = self._template.format(self._next)
        self._next += 1
        return value


def sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:]


def join_sentences(parts: list[str]) -> str:
    cased = (sentence_case(part.strip()) for part in parts if part.strip())
    return " ".join(
        part if part.endswith((".", "?", "!")) else f"{part}." for part in cased
    )


def pick_sex(rng: random.Random) -> str:
    return rng.choices(("female", "male", "other", "unknown"), weights=(48, 48, 3, 1))[
        0
    ]


def pick_date_of_birth(rng: random.Random) -> date:
    return ANCHOR_DATE - timedelta(days=rng.randrange(19 * 365, 89 * 365))


def pick_document_date(rng: random.Random) -> date:
    return ANCHOR_DATE - timedelta(days=rng.randrange(0, DOCUMENT_HISTORY_DAYS))


def build_patient(rng: random.Random, practice_id: str, patient_id: str) -> Patient:
    return Patient(
        id=patient_id,
        practice_id=practice_id,
        mrn=f"MRN-{patient_id.removeprefix('patient-')}",
        first_name=rng.choice(FIRST_NAMES),
        last_name=rng.choice(LAST_NAMES),
        date_of_birth=pick_date_of_birth(rng),
        sex=pick_sex(rng),
    )


def format_vitals(rng: random.Random) -> str:
    return (
        f"Blood pressure {rng.randrange(102, 168)}/{rng.randrange(58, 102)} mmHg, "
        f"pulse {rng.randrange(52, 118)} bpm, "
        f"temperature {rng.randrange(360, 391) / 10:.1f} C, "
        f"oxygen saturation {rng.randrange(90, 100)} percent on room air."
    )


def describe_presentation(rng: random.Random, ctx: RenderContext) -> str:
    if ctx.voice == "lay":
        return rng.choice(ctx.condition.lay_symptoms)
    return rng.choice(ctx.condition.clinical_symptoms)


def compose_history(rng: random.Random, ctx: RenderContext) -> str:
    condition = ctx.condition
    parts = [f"{ctx.age}-year-old presenting with {describe_presentation(rng, ctx)}"]
    parts.append(rng.choice(condition.clinical_symptoms))
    remaining = [s for s in condition.clinical_symptoms if s != parts[-1]]
    if remaining:
        parts.append(rng.choice(remaining))
    parts.append(f"Symptoms have been present for {rng.choice(DURATIONS)}")
    parts.append(rng.choice(ONSET_PHRASES))
    parts.append(rng.choice(FUNCTIONAL_IMPACTS))
    parts.append(rng.choice(SOCIAL_CONTEXTS))
    return join_sentences(parts)


def compose_review_of_systems(rng: random.Random, ctx: RenderContext) -> str:
    condition = ctx.condition
    parts = [f"Positive for {rng.choice(condition.clinical_symptoms)}"]
    safe_distractors = filler_distractor_keys(condition)
    if safe_distractors:
        other = CONDITIONS_BY_KEY[rng.choice(safe_distractors)]
        parts.append(f"Specifically denies {rng.choice(other.clinical_symptoms)}")
    parts.append("No fevers, night sweats, or unintentional weight change otherwise")
    return join_sentences(parts)


def compose_examination(rng: random.Random, ctx: RenderContext) -> str:
    findings = list(ctx.condition.exam_findings)
    rng.shuffle(findings)
    return join_sentences([format_vitals(rng), *findings[:2]])


def compose_plan(rng: random.Random, ctx: RenderContext) -> str:
    return join_sentences(
        [
            rng.choice(ctx.condition.plans),
            rng.choice(ADHERENCE_NOTES),
            rng.choice(FOLLOW_UP_NOTES),
        ]
    )


def render_diagnostic_note(rng: random.Random, ctx: RenderContext) -> str:
    return "\n\n".join(
        (
            f"CHIEF COMPLAINT\n{sentence_case(describe_presentation(rng, ctx))}.",
            f"HISTORY OF PRESENT ILLNESS\n{compose_history(rng, ctx)}",
            f"REVIEW OF SYSTEMS\n{compose_review_of_systems(rng, ctx)}",
            f"PHYSICAL EXAMINATION\n{compose_examination(rng, ctx)}",
            f"ASSESSMENT\n{rng.choice(ctx.condition.impressions)}.",
            f"PLAN\n{compose_plan(rng, ctx)}",
        )
    )


def render_specialist_note(rng: random.Random, ctx: RenderContext) -> str:
    return "\n\n".join(
        (
            f"REASON FOR REFERRAL\n{ctx.condition.specialty} opinion requested for a "
            f"{ctx.age}-year-old with {describe_presentation(rng, ctx)}.",
            f"INTERVAL HISTORY\n{compose_history(rng, ctx)}",
            f"EXAMINATION\n{compose_examination(rng, ctx)}",
            f"IMPRESSION\n{rng.choice(ctx.condition.impressions)}.",
            f"RECOMMENDATIONS\n{compose_plan(rng, ctx)}",
        )
    )


def render_radiology_report(rng: random.Random, ctx: RenderContext) -> str:
    return "\n\n".join(
        (
            f"CLINICAL INDICATION\n{ctx.age}-year-old. "
            f"{sentence_case(describe_presentation(rng, ctx))}.",
            "TECHNIQUE\nStandard departmental protocol. Comparison made with any available prior imaging.",
            f"FINDINGS\n{rng.choice(ctx.condition.imaging_findings)}",
            f"IMPRESSION\n{rng.choice(ctx.condition.impressions)}. "
            f"{rng.choice(FOLLOW_UP_NOTES)}",
        )
    )


def render_lab_report(rng: random.Random, ctx: RenderContext) -> str:
    return "\n\n".join(
        (
            "SPECIMEN\nVenous blood, fasting where applicable. Collected by phlebotomy.",
            f"RESULTS\n{rng.choice(ctx.condition.lab_findings)}.",
            f"INTERPRETATION\nRequested for a {ctx.age}-year-old with "
            f"{describe_presentation(rng, ctx)}. {rng.choice(ctx.condition.impressions)}.",
            f"COMMENT\n{rng.choice(ctx.condition.plans)}. {rng.choice(FOLLOW_UP_NOTES)}",
        )
    )


RENDERERS = {
    "diagnostic_note": render_diagnostic_note,
    "specialist_note": render_specialist_note,
    "radiology_report": render_radiology_report,
    "lab_report": render_lab_report,
}

TITLE_TEMPLATES = {
    "diagnostic_note": (
        "Consultation Note",
        "Review Appointment",
        "Acute Presentation",
    ),
    "specialist_note": (
        "{specialty} Follow-Up",
        "{specialty} Opinion",
        "{specialty} Assessment",
    ),
    "radiology_report": ("Diagnostic Imaging Report", "Imaging Study Report"),
    "lab_report": ("Laboratory Interpretation", "Pathology Interpretation"),
}


def build_title(rng: random.Random, condition: Condition, document_type: str) -> str:
    return rng.choice(TITLE_TEMPLATES[document_type]).format(
        specialty=condition.specialty
    )


def render_negated_body(rng: random.Random, ctx: RenderContext) -> str:
    condition = ctx.condition
    negation = (
        rng.choice(condition.negations)
        if condition.negations
        else f"Presentation is not consistent with {condition.label.lower()}."
    )
    safe_distractors = filler_distractor_keys(condition)
    alternative = (
        CONDITIONS_BY_KEY[rng.choice(safe_distractors)]
        if safe_distractors
        else condition
    )
    alt_ctx = RenderContext(
        condition=alternative, voice="clinical", age=ctx.age, sex=ctx.sex
    )
    return "\n\n".join(
        (
            f"CHIEF COMPLAINT\nAssessment to exclude {condition.label.lower()}.",
            f"HISTORY OF PRESENT ILLNESS\n{join_sentences([negation, rng.choice(alternative.clinical_symptoms), rng.choice(SOCIAL_CONTEXTS)])}",
            f"REVIEW OF SYSTEMS\nScreening questions for {condition.label.lower()} were negative throughout.",
            f"PHYSICAL EXAMINATION\n{compose_examination(rng, alt_ctx)}",
            f"ASSESSMENT\n{condition.label} considered and excluded. {rng.choice(alternative.impressions)}.",
            f"PLAN\n{compose_plan(rng, alt_ctx)}",
        )
    )


def render_historical_body(rng: random.Random, ctx: RenderContext) -> str:
    condition = ctx.condition
    years = rng.randrange(4, 15)
    return "\n\n".join(
        (
            "CHIEF COMPLAINT\nRoutine review. Currently asymptomatic.",
            "HISTORY OF PRESENT ILLNESS\n"
            + join_sentences(
                [
                    f"{ctx.age}-year-old with a past history of {condition.label.lower()}, "
                    f"diagnosed {years} years ago and quiescent since",
                    f"Previously described {rng.choice(condition.clinical_symptoms)}, "
                    "none of which is active today",
                    "No treatment is required at present",
                    rng.choice(SOCIAL_CONTEXTS),
                ]
            ),
            "REVIEW OF SYSTEMS\nNo active symptoms reported in any system.",
            f"PHYSICAL EXAMINATION\n{format_vitals(rng)} Examination unremarkable today.",
            f"ASSESSMENT\n{condition.label} in long-term remission. No active disease.",
            f"PLAN\nContinue routine surveillance. {rng.choice(FOLLOW_UP_NOTES)}",
        )
    )


@dataclass(frozen=True)
class DocumentPlan:
    condition: Condition
    document_type: str
    voice: str


def build_document(
    rng: random.Random,
    patient: Patient,
    document_id: str,
    plan: DocumentPlan,
) -> Document:
    ctx = RenderContext(
        condition=plan.condition, voice=plan.voice, age=patient.age, sex=patient.sex
    )
    if plan.voice == "negated":
        body = render_negated_body(rng, ctx)
    elif plan.voice == "historical":
        body = render_historical_body(rng, ctx)
    else:
        body = RENDERERS[plan.document_type](rng, ctx)
    return Document(
        id=document_id,
        practice_id=patient.practice_id,
        patient_id=patient.id,
        document_type=plan.document_type,
        title=build_title(rng, plan.condition, plan.document_type),
        document_date=pick_document_date(rng),
        author_name=rng.choice(CLINICIAN_NAMES),
        body=body,
    )


def build_curated_evidence_document(
    rng: random.Random,
    patient: Patient,
    document_id: str,
    case: CuratedCase,
) -> Document:
    condition = CONDITIONS_BY_KEY[case.condition_key]
    clinical = list(condition.clinical_symptoms)
    rng.shuffle(clinical)
    quotes = select_patient_quotes(case.query, condition.lay_symptoms)
    body = "\n\n".join(
        (
            f"REASON FOR REFERRAL\n{condition.specialty} opinion for a {patient.age}-year-old. "
            f"{sentence_case(clinical[0])}.",
            "PATIENT-REPORTED HISTORY\n"
            + " ".join(f"The patient describes {quote}." for quote in quotes),
            f"HISTORY OF PRESENT ILLNESS\n{join_sentences(clinical[1:3] or clinical[:1])}",
            f"EXAMINATION\n{join_sentences(list(condition.exam_findings)[:2])}",
            f"IMPRESSION\n{rng.choice(condition.impressions)}.",
            f"RECOMMENDATIONS\n{rng.choice(condition.plans)}. {rng.choice(FOLLOW_UP_NOTES)}",
        )
    )
    return Document(
        id=document_id,
        practice_id=patient.practice_id,
        patient_id=patient.id,
        document_type="specialist_note",
        title=f"{condition.specialty} Follow-Up",
        document_date=pick_document_date(rng),
        author_name=rng.choice(CLINICIAN_NAMES),
        body=body,
    )


def build_curated_supporting_document(
    rng: random.Random,
    patient: Patient,
    document_id: str,
    case: CuratedCase,
) -> Document:
    condition = CONDITIONS_BY_KEY[case.condition_key]
    body = "\n\n".join(
        (
            "SPECIMEN\nVenous blood, fasting where applicable. Collected by phlebotomy.",
            f"RESULTS\n{rng.choice(condition.lab_findings)}.",
            f"INTERPRETATION\n{sentence_case(rng.choice(condition.clinical_symptoms))}. "
            f"{rng.choice(condition.impressions)}.",
            f"COMMENT\n{rng.choice(condition.plans)}. {rng.choice(FOLLOW_UP_NOTES)}",
        )
    )
    return Document(
        id=document_id,
        practice_id=patient.practice_id,
        patient_id=patient.id,
        document_type="lab_report",
        title="Laboratory Interpretation",
        document_date=pick_document_date(rng),
        author_name=rng.choice(CLINICIAN_NAMES),
        body=body,
    )


def build_decoy_document(
    rng: random.Random,
    patient: Patient,
    document_id: str,
    case: CuratedCase,
) -> Document:
    condition = CONDITIONS_BY_KEY[case.condition_key]
    body = "\n\n".join(
        (
            f"CHIEF COMPLAINT\n{sentence_case(case.query)}.",
            "HISTORY OF PRESENT ILLNESS\n"
            + join_sentences(
                [
                    f"{patient.age}-year-old who describes {case.query}",
                    rng.choice(condition.clinical_symptoms),
                    rng.choice(condition.lay_symptoms),
                    rng.choice(SOCIAL_CONTEXTS),
                ]
            ),
            f"REVIEW OF SYSTEMS\nPositive for {case.query}.",
            f"PHYSICAL EXAMINATION\n{format_vitals(rng)} "
            f"{sentence_case(rng.choice(condition.exam_findings))}.",
            f"ASSESSMENT\n{rng.choice(condition.impressions)}.",
            f"PLAN\n{rng.choice(condition.plans)}. {rng.choice(FOLLOW_UP_NOTES)}",
        )
    )
    return Document(
        id=document_id,
        practice_id=patient.practice_id,
        patient_id=patient.id,
        document_type="diagnostic_note",
        title="Consultation Note",
        document_date=pick_document_date(rng),
        author_name=rng.choice(CLINICIAN_NAMES),
        body=body,
    )


PATHOLOGICAL_TITLES = (
    "Scanned Referral (Text Extraction Incomplete)",
    "Imported Note (Empty Payload)",
    "Bulk Import Fragment",
    "Fax Cover Sheet",
    "Legacy Migration Artefact",
    "Dictation Upload (Unsegmented)",
)


def build_pathological_bodies() -> tuple[str, ...]:
    unsegmented = " ".join(
        [
            "patient reviewed in clinic observations stable no acute concerns documented "
            "medication list reconciled follow up arranged as previously agreed"
        ]
        * 700
    )
    return (
        "",
        "   \n\t   \n  ",
        unsegmented,
        "--- ... *** /// ### ... --- ... ***",
        "Note​​​content­­with‎‏directionaĺ́marks﻿ and combining diacritics.",
        "clinicalnotefragment" * 400,
    )


def allocate_filler_documents(
    rng: random.Random, condition: Condition
) -> list[DocumentPlan]:
    count = rng.choices((2, 3, 4, 5, 6), weights=(28, 32, 20, 13, 7))[0]
    safe_distractors = filler_distractor_keys(condition)
    plans = [DocumentPlan(condition, "diagnostic_note", "lay")]
    for _ in range(count - 1):
        roll = rng.random()
        if roll < 0.06 and condition.negations:
            plans.append(DocumentPlan(condition, "diagnostic_note", "negated"))
        elif roll < 0.11:
            plans.append(DocumentPlan(condition, "diagnostic_note", "historical"))
        elif roll < 0.28 and safe_distractors:
            other = CONDITIONS_BY_KEY[rng.choice(safe_distractors)]
            plans.append(DocumentPlan(other, rng.choice(DOCUMENT_TYPES), "clinical"))
        else:
            plans.append(
                DocumentPlan(condition, rng.choice(DOCUMENT_TYPES), "clinical")
            )
    return plans


@dataclass
class Dataset:
    patients: list[Patient]
    documents: list[Document]
    cases: list[dict[str, object]]


def generate() -> Dataset:
    rng = random.Random(SEED)
    patient_ids = Sequence("patient-{:04d}")
    document_ids = Sequence("document-{:06d}")

    patients: list[Patient] = []
    documents: list[Document] = []
    cases: list[dict[str, object]] = []
    used = {spec.id: 0 for spec in PRACTICE_SPECS}

    def add_patient(practice_id: str) -> Patient:
        patient = build_patient(rng, practice_id, patient_ids.take())
        patients.append(patient)
        return patient

    def add_document(patient: Patient, plan: DocumentPlan) -> Document:
        document = build_document(rng, patient, document_ids.take(), plan)
        documents.append(document)
        used[patient.practice_id] += 1
        return document

    unrelated_pool = tuple(
        c
        for c in FILLER_CONDITIONS
        if c.key
        not in {k for case in CURATED_CASES for k in case.distractor_condition_keys}
    )

    for case in CURATED_CASES:
        condition = CONDITIONS_BY_KEY[case.condition_key]

        expected = add_patient(PRIMARY_PRACTICE.id)
        evidence = build_curated_evidence_document(
            rng, expected, document_ids.take(), case
        )
        documents.append(evidence)
        used[expected.practice_id] += 1
        supporting = build_curated_supporting_document(
            rng, expected, document_ids.take(), case
        )
        documents.append(supporting)
        used[expected.practice_id] += 1
        add_document(
            expected,
            DocumentPlan(rng.choice(unrelated_pool), "diagnostic_note", "clinical"),
        )

        decoy = add_patient(case.decoy_practice_id)
        decoy_document = build_decoy_document(rng, decoy, document_ids.take(), case)
        documents.append(decoy_document)
        used[decoy.practice_id] += 1
        add_document(decoy, DocumentPlan(condition, "radiology_report", "clinical"))

        distractor_ids: list[str] = []
        for key in case.distractor_condition_keys:
            distractor = add_patient(PRIMARY_PRACTICE.id)
            distractor_ids.append(distractor.id)
            add_document(
                distractor,
                DocumentPlan(CONDITIONS_BY_KEY[key], "diagnostic_note", "lay"),
            )
            add_document(
                distractor,
                DocumentPlan(CONDITIONS_BY_KEY[key], "specialist_note", "clinical"),
            )

        cases.append(
            {
                "id": case.id,
                "query": case.query,
                "conditionKey": case.condition_key,
                "expectedPatientId": expected.id,
                "expectedDocumentId": evidence.id,
                "expectedMatchingDocumentCount": 2,
                "crossPracticeDecoyPatientId": decoy.id,
                "crossPracticeDecoyPracticeId": decoy.practice_id,
                "crossPracticeDecoyDocumentId": decoy_document.id,
                "inPracticeDistractorPatientIds": distractor_ids,
            }
        )

    pathological_patient = add_patient(PRIMARY_PRACTICE.id)
    for index, body in enumerate(build_pathological_bodies()):
        documents.append(
            Document(
                id=document_ids.take(),
                practice_id=pathological_patient.practice_id,
                patient_id=pathological_patient.id,
                document_type="diagnostic_note"
                if index % 2 == 0
                else "specialist_note",
                title=PATHOLOGICAL_TITLES[index],
                document_date=pick_document_date(rng),
                author_name=rng.choice(CLINICIAN_NAMES),
                body=body,
            )
        )
        used[pathological_patient.practice_id] += 1

    for spec in PRACTICE_SPECS:
        while used[spec.id] < spec.document_budget:
            patient = add_patient(spec.id)
            condition = rng.choice(FILLER_CONDITIONS)
            for plan in allocate_filler_documents(rng, condition):
                if used[spec.id] >= spec.document_budget:
                    break
                add_document(patient, plan)

    return Dataset(patients=patients, documents=documents, cases=cases)


def write_csv(
    path: Path, header: tuple[str, ...], rows: list[tuple[object, ...]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n", quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        writer.writerows(rows)


def build_user_rows() -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for spec in PRACTICE_SPECS:
        for index, (role, display_name) in enumerate(STAFF_TEMPLATE, start=1):
            rows.append(
                (
                    f"user-{spec.slug}-{index:02d}",
                    spec.id,
                    display_name,
                    f"{role}.{spec.slug}@example-clinic.invalid",
                    role,
                )
            )
    return rows


def write_dataset(dataset: Dataset, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        out_dir / "practices.csv",
        ("id", "name", "slug", "city", "region"),
        [(s.id, s.name, s.slug, s.city, s.region) for s in PRACTICE_SPECS],
    )
    write_csv(
        out_dir / "users.csv",
        ("id", "practice_id", "display_name", "email", "role"),
        build_user_rows(),
    )
    write_csv(
        out_dir / "patients.csv",
        ("id", "practice_id", "mrn", "first_name", "last_name", "date_of_birth", "sex"),
        [
            (
                p.id,
                p.practice_id,
                p.mrn,
                p.first_name,
                p.last_name,
                p.date_of_birth.isoformat(),
                p.sex,
            )
            for p in dataset.patients
        ],
    )
    write_csv(
        out_dir / "clinical_documents.csv",
        (
            "id",
            "practice_id",
            "patient_id",
            "document_type",
            "title",
            "document_date",
            "author_name",
            "body",
        ),
        [
            (
                d.id,
                d.practice_id,
                d.patient_id,
                d.document_type,
                d.title,
                d.document_date.isoformat(),
                d.author_name,
                d.body,
            )
            for d in dataset.documents
        ],
    )

    manifest = {
        "seed": SEED,
        "anchorDate": ANCHOR_DATE.isoformat(),
        "primaryPracticeId": PRIMARY_PRACTICE.id,
        "practiceCount": len(PRACTICE_SPECS),
        "patientCount": len(dataset.patients),
        "documentCount": len(dataset.documents),
        "pathologicalDocumentCount": len(build_pathological_bodies()),
        "cases": dataset.cases,
    }
    (out_dir / "curated_cases.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def report_duplicate_bodies(dataset: Dataset) -> int:
    seen: dict[str, int] = {}
    for document in dataset.documents:
        key = document.body.strip()
        if not key:
            continue
        seen[key] = seen.get(key, 0) + 1
    return sum(count - 1 for count in seen.values() if count > 1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the synthetic clinical dataset."
    )
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).resolve().parent / "data"
    )
    args = parser.parse_args()

    dataset = generate()
    if len(dataset.documents) != TOTAL_DOCUMENT_TARGET:
        print(
            f"expected {TOTAL_DOCUMENT_TARGET} documents, generated {len(dataset.documents)}",
            file=sys.stderr,
        )
        return 1

    duplicates = report_duplicate_bodies(dataset)
    write_dataset(dataset, args.out)
    print(f"practices:         {len(PRACTICE_SPECS)}")
    print(f"patients:          {len(dataset.patients)}")
    print(f"documents:         {len(dataset.documents)}")
    print(f"curated cases:     {len(dataset.cases)}")
    print(f"duplicate bodies:  {duplicates}")
    print(f"written to:        {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
