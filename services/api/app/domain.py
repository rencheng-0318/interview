from enum import StrEnum


class DocumentType(StrEnum):
    DIAGNOSTIC_NOTE = "diagnostic_note"
    SPECIALIST_NOTE = "specialist_note"
    RADIOLOGY_REPORT = "radiology_report"
    LAB_REPORT = "lab_report"
