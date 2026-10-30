import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

INPUT_CONFIG = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _blank_to_none(value):
    if isinstance(value, str) and not value.strip():
        return None
    return value


def _validate_person_name(value: str) -> str:
    if not all(ch.isalpha() or ch in " .'-" for ch in value):
        raise ValueError("Name may only contain letters, spaces, dots, apostrophes and hyphens.")
    return value


class DomainLab(str, Enum):

    full_stack_saas = "full_stack_saas"
    python_backend = "python_backend"
    ai_vector = "ai_vector"
    frontend_ops = "frontend_ops"
    qa_automation = "qa_automation"
    uiux_design = "uiux_design"




class InquiryCreate(BaseModel):

    model_config = INPUT_CONFIG

    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr  # checks real email syntax (needs the email-validator package)
    company: str | None = Field(default=None, max_length=120)  # optional
    industry: str | None = Field(default=None, max_length=80)  # optional
    message: str = Field(min_length=10, max_length=2000)

    _blank_optionals = field_validator("company", "industry", mode="before")(_blank_to_none)
    _check_name = field_validator("full_name")(_validate_person_name)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class InquiryOut(BaseModel):

    id: int
    full_name: str
    email: str
    company: str | None
    industry: str | None
    message: str
    created_at: str

class EnrollmentCreate(BaseModel):

    model_config = INPUT_CONFIG

    full_name: str = Field(min_length=2, max_length=100)
    college: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str
    domain_lab: DomainLab
    referral_code: str | None = Field(default=None, max_length=40)
    goals: str | None = Field(default=None, max_length=1000)

    _blank_optionals = field_validator("referral_code", "goals", mode="before")(_blank_to_none)
    _check_name = field_validator("full_name")(_validate_person_name)

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("phone")
    @classmethod
    def normalise_phone(cls, value: str) -> str:
        cleaned = re.sub(r"[\s\-()]", "", value)
        if not re.fullmatch(r"\+?\d{10,13}", cleaned):
            raise ValueError("Enter a valid phone number (10-13 digits, optional leading +).")
        return cleaned


class EnrollmentOut(BaseModel):
    id: int
    full_name: str
    college: str
    email: str
    phone: str
    domain_lab: str
    referral_code: str | None
    goals: str | None
    status: str
    created_at: str
