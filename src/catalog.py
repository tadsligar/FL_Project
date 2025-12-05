"""
Fixed specialty catalog to prevent hallucination.
Defines all medical specialties with metadata for scoring.
"""

from typing import Literal
from pydantic import BaseModel, Field


class Specialty(BaseModel):
    """A medical specialty with metadata for relevance scoring."""

    id: str = Field(..., description="Unique identifier")
    display_name: str = Field(..., description="Human-readable name")
    type: Literal["generalist", "medical", "surgical"] = Field(..., description="Specialty category")
    emergency_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relevance to emergency/acute cases"
    )
    pediatric_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relevance to pediatric cases"
    )
    adult_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Relevance to adult cases"
    )
    procedural_signal: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Likelihood of procedural/surgical intervention"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords associated with this specialty"
    )


# ============================================================================
# Fixed Specialty Catalog
# ============================================================================

SPECIALTY_CATALOG: list[Specialty] = [
    # Generalists
    Specialty(
        id="emergency_medicine",
        display_name="Emergency Medicine",
        type="generalist",
        emergency_weight=1.0,
        pediatric_weight=0.7,
        adult_weight=0.9,
        procedural_signal=0.3,
        keywords=[
            "acute", "emergency", "trauma", "unstable", "shock", "syncope",
            "chest pain", "stroke", "seizure", "overdose", "critical"
        ]
    ),
    Specialty(
        id="pediatrics",
        display_name="Pediatrics",
        type="generalist",
        emergency_weight=0.6,
        pediatric_weight=1.0,
        adult_weight=0.0,
        procedural_signal=0.1,
        keywords=[
            "child", "infant", "newborn", "adolescent", "pediatric",
            "congenital", "developmental", "vaccination", "growth"
        ]
    ),
    Specialty(
        id="family_internal_medicine",
        display_name="Family/Internal Medicine",
        type="generalist",
        emergency_weight=0.4,
        pediatric_weight=0.5,
        adult_weight=1.0,
        procedural_signal=0.1,
        keywords=[
            "chronic", "primary care", "preventive", "screening",
            "hypertension", "diabetes", "hyperlipidemia", "wellness"
        ]
    ),

    # Medical Specialties
    Specialty(
        id="neurology",
        display_name="Neurology",
        type="medical",
        emergency_weight=0.7,
        pediatric_weight=0.6,
        adult_weight=0.9,
        procedural_signal=0.2,
        keywords=[
            "headache", "seizure", "stroke", "weakness", "numbness",
            "tremor", "dementia", "multiple sclerosis", "parkinson",
            "neuropathy", "altered mental status", "coma"
        ]
    ),
    Specialty(
        id="psychiatry",
        display_name="Psychiatry",
        type="medical",
        emergency_weight=0.5,
        pediatric_weight=0.6,
        adult_weight=0.9,
        procedural_signal=0.0,
        keywords=[
            "depression", "anxiety", "psychosis", "bipolar", "schizophrenia",
            "suicidal", "mania", "delusions", "hallucinations", "behavior"
        ]
    ),
    Specialty(
        id="dermatology",
        display_name="Dermatology",
        type="medical",
        emergency_weight=0.2,
        pediatric_weight=0.6,
        adult_weight=0.8,
        procedural_signal=0.3,
        keywords=[
            "rash", "skin", "lesion", "pruritus", "acne", "melanoma",
            "psoriasis", "eczema", "dermatitis", "urticaria", "biopsy"
        ]
    ),
    Specialty(
        id="ophthalmology",
        display_name="Ophthalmology",
        type="medical",
        emergency_weight=0.3,
        pediatric_weight=0.5,
        adult_weight=0.8,
        procedural_signal=0.5,
        keywords=[
            "vision", "eye", "blindness", "glaucoma", "cataract",
            "retina", "diplopia", "visual loss", "red eye"
        ]
    ),
    Specialty(
        id="ent",
        display_name="Otolaryngology (ENT)",
        type="medical",
        emergency_weight=0.3,
        pediatric_weight=0.7,
        adult_weight=0.7,
        procedural_signal=0.6,
        keywords=[
            "ear", "nose", "throat", "hearing loss", "tinnitus",
            "sinusitis", "vertigo", "dysphagia", "hoarseness"
        ]
    ),
    Specialty(
        id="obgyn",
        display_name="Obstetrics & Gynecology",
        type="medical",
        emergency_weight=0.5,
        pediatric_weight=0.0,
        adult_weight=0.9,
        procedural_signal=0.7,
        keywords=[
            "pregnancy", "vaginal bleeding", "pelvic pain", "menstrual",
            "prenatal", "labor", "delivery", "menopause", "ovarian"
        ]
    ),
    Specialty(
        id="cardiology",
        display_name="Cardiology",
        type="medical",
        emergency_weight=0.8,
        pediatric_weight=0.4,
        adult_weight=1.0,
        procedural_signal=0.4,
        keywords=[
            "chest pain", "MI", "heart failure", "arrhythmia", "hypertension",
            "angina", "palpitations", "dyspnea", "edema", "CAD"
        ]
    ),
    Specialty(
        id="endocrinology",
        display_name="Endocrinology",
        type="medical",
        emergency_weight=0.5,
        pediatric_weight=0.6,
        adult_weight=0.9,
        procedural_signal=0.1,
        keywords=[
            "diabetes", "thyroid", "hyperglycemia", "hypoglycemia",
            "adrenal", "pituitary", "hyperthyroid", "hypothyroid", "DKA"
        ]
    ),
    Specialty(
        id="gastroenterology",
        display_name="Gastroenterology",
        type="medical",
        emergency_weight=0.6,
        pediatric_weight=0.5,
        adult_weight=0.9,
        procedural_signal=0.4,
        keywords=[
            "abdominal pain", "GI bleed", "diarrhea", "constipation",
            "IBD", "cirrhosis", "hepatitis", "pancreatitis", "GERD"
        ]
    ),
    Specialty(
        id="hematology",
        display_name="Hematology",
        type="medical",
        emergency_weight=0.6,
        pediatric_weight=0.6,
        adult_weight=0.9,
        procedural_signal=0.2,
        keywords=[
            "anemia", "bleeding", "thrombosis", "leukemia", "lymphoma",
            "coagulation", "DVT", "PE", "thrombocytopenia"
        ]
    ),
    Specialty(
        id="infectious_disease",
        display_name="Infectious Disease",
        type="medical",
        emergency_weight=0.7,
        pediatric_weight=0.7,
        adult_weight=0.9,
        procedural_signal=0.1,
        keywords=[
            "fever", "infection", "sepsis", "HIV", "tuberculosis",
            "meningitis", "pneumonia", "abscess", "bacteremia"
        ]
    ),
    Specialty(
        id="nephrology",
        display_name="Nephrology",
        type="medical",
        emergency_weight=0.6,
        pediatric_weight=0.5,
        adult_weight=0.9,
        procedural_signal=0.3,
        keywords=[
            "renal failure", "dialysis", "hematuria", "proteinuria",
            "AKI", "CKD", "electrolyte", "hypertension", "edema"
        ]
    ),
    Specialty(
        id="oncology",
        display_name="Oncology",
        type="medical",
        emergency_weight=0.5,
        pediatric_weight=0.5,
        adult_weight=0.9,
        procedural_signal=0.3,
        keywords=[
            "cancer", "tumor", "malignancy", "chemotherapy", "radiation",
            "metastasis", "lymphoma", "carcinoma", "mass"
        ]
    ),
    Specialty(
        id="pulmonology",
        display_name="Pulmonology",
        type="medical",
        emergency_weight=0.7,
        pediatric_weight=0.6,
        adult_weight=0.9,
        procedural_signal=0.3,
        keywords=[
            "dyspnea", "cough", "COPD", "asthma", "pneumonia",
            "respiratory failure", "PE", "pleural effusion", "hypoxia"
        ]
    ),
    Specialty(
        id="rheumatology",
        display_name="Rheumatology",
        type="medical",
        emergency_weight=0.3,
        pediatric_weight=0.5,
        adult_weight=0.9,
        procedural_signal=0.2,
        keywords=[
            "arthritis", "joint pain", "autoimmune", "lupus", "RA",
            "gout", "vasculitis", "connective tissue", "inflammatory"
        ]
    ),
    Specialty(
        id="geriatrics",
        display_name="Geriatrics",
        type="medical",
        emergency_weight=0.5,
        pediatric_weight=0.0,
        adult_weight=1.0,
        procedural_signal=0.1,
        keywords=[
            "elderly", "dementia", "fall", "frailty", "polypharmacy",
            "delirium", "geriatric", "aging"
        ]
    ),
    Specialty(
        id="allergy_immunology",
        display_name="Allergy & Immunology",
        type="medical",
        emergency_weight=0.5,
        pediatric_weight=0.7,
        adult_weight=0.7,
        procedural_signal=0.1,
        keywords=[
            "allergy", "anaphylaxis", "asthma", "immunodeficiency",
            "urticaria", "angioedema", "allergic reaction"
        ]
    ),
    Specialty(
        id="sleep_medicine",
        display_name="Sleep Medicine",
        type="medical",
        emergency_weight=0.2,
        pediatric_weight=0.5,
        adult_weight=0.8,
        procedural_signal=0.1,
        keywords=[
            "insomnia", "sleep apnea", "narcolepsy", "fatigue",
            "snoring", "hypersomnia"
        ]
    ),
    Specialty(
        id="urology",
        display_name="Urology",
        type="medical",
        emergency_weight=0.5,
        pediatric_weight=0.4,
        adult_weight=0.9,
        procedural_signal=0.7,
        keywords=[
            "urinary", "hematuria", "kidney stone", "prostate", "UTI",
            "incontinence", "retention", "dysuria", "testicular"
        ]
    ),
    Specialty(
        id="sports_medicine",
        display_name="Sports Medicine",
        type="medical",
        emergency_weight=0.3,
        pediatric_weight=0.6,
        adult_weight=0.7,
        procedural_signal=0.4,
        keywords=[
            "sports injury", "ACL", "concussion", "fracture",
            "sprain", "strain", "athletic"
        ]
    ),

    # Surgical Specialties
    Specialty(
        id="general_surgery",
        display_name="General Surgery",
        type="surgical",
        emergency_weight=0.7,
        pediatric_weight=0.5,
        adult_weight=0.9,
        procedural_signal=1.0,
        keywords=[
            "appendicitis", "cholecystitis", "hernia", "bowel obstruction",
            "acute abdomen", "peritonitis", "surgical abdomen"
        ]
    ),
    Specialty(
        id="orthopedic_surgery",
        display_name="Orthopedic Surgery",
        type="surgical",
        emergency_weight=0.6,
        pediatric_weight=0.6,
        adult_weight=0.9,
        procedural_signal=0.9,
        keywords=[
            "fracture", "dislocation", "joint pain", "back pain",
            "trauma", "bone", "ligament", "tendon"
        ]
    ),
    Specialty(
        id="vascular_surgery",
        display_name="Vascular Surgery",
        type="surgical",
        emergency_weight=0.8,
        pediatric_weight=0.2,
        adult_weight=1.0,
        procedural_signal=0.9,
        keywords=[
            "aneurysm", "claudication", "ischemia", "vascular",
            "arterial", "venous", "AAA", "peripheral vascular"
        ]
    ),
    Specialty(
        id="plastic_surgery",
        display_name="Plastic Surgery",
        type="surgical",
        emergency_weight=0.3,
        pediatric_weight=0.5,
        adult_weight=0.8,
        procedural_signal=1.0,
        keywords=[
            "reconstruction", "burn", "laceration", "cosmetic",
            "hand surgery", "facial trauma"
        ]
    ),
    Specialty(
        id="thoracic_surgery",
        display_name="Thoracic Surgery",
        type="surgical",
        emergency_weight=0.7,
        pediatric_weight=0.3,
        adult_weight=0.9,
        procedural_signal=1.0,
        keywords=[
            "lung cancer", "esophageal", "mediastinal", "chest trauma",
            "pneumothorax", "empyema"
        ]
    ),
]


# ============================================================================
# Catalog utilities
# ============================================================================

def get_catalog() -> list[Specialty]:
    """Return the complete specialty catalog."""
    return SPECIALTY_CATALOG


def get_specialty_by_id(specialty_id: str) -> Specialty | None:
    """Lookup a specialty by ID."""
    for spec in SPECIALTY_CATALOG:
        if spec.id == specialty_id:
            return spec
    return None


def get_specialty_ids() -> list[str]:
    """Return all specialty IDs."""
    return [spec.id for spec in SPECIALTY_CATALOG]


def validate_specialty_ids(ids: list[str]) -> tuple[bool, list[str]]:
    """
    Validate that all IDs are in the catalog.
    Returns (is_valid, invalid_ids).
    """
    valid_ids = set(get_specialty_ids())
    invalid = [sid for sid in ids if sid not in valid_ids]
    return len(invalid) == 0, invalid


def get_generalist_ids() -> list[str]:
    """Return IDs of generalist specialties."""
    return [spec.id for spec in SPECIALTY_CATALOG if spec.type == "generalist"]
