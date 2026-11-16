from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

COUNTRIES = {"TR", "DE", "AT", "CH", "NL", "DK", "SE", "NO", "GB", "BE"}
Role = Literal["applied_ai", "rag_llm", "automation", "data_bi", "graduate_ml"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProfileInput(Input):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    location: str = Field(min_length=2, max_length=160)
    source_id: str


class FactInput(Input):
    section: Literal["summary", "experience", "education", "skills", "projects", "languages"]
    text: str = Field(min_length=3, max_length=1800)
    source_page: int = Field(ge=1)
    source_quote: str = Field(min_length=3, max_length=3000)
    tags: list[str] = Field(default_factory=list, max_length=30)


class CompanyInput(Input):
    name: str = Field(min_length=2, max_length=200)
    domain: str = Field(min_length=3, max_length=253, pattern=r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    country: str
    source_url: HttpUrl

    @field_validator("country")
    @classmethod
    def country_allowed(cls, value):
        if value.upper() not in COUNTRIES:
            raise ValueError("country is outside the initial target strategy")
        return value.upper()

    @field_validator("domain")
    @classmethod
    def lower_domain(cls, value):
        return value.lower().removeprefix("www.")


class OpportunityInput(Input):
    company_id: str
    external_key: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=2, max_length=200)
    kind: Literal["vacancy", "speculative"]
    role: Role
    description: str = Field(min_length=3, max_length=30000)
    source_url: HttpUrl
    eligibility: Literal["eligible", "ineligible", "unknown"] = "unknown"
    required_languages: list[str] = Field(default_factory=list, max_length=10)


class ContactInput(Input):
    company_id: str
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    title: str = Field(min_length=2, max_length=160)
    evidence_type: Literal[
        "published_named", "published_functional", "user_confirmed", "inferred_or_unconfirmed"
    ]
    source_url: HttpUrl
    source_quote: str = Field(min_length=3, max_length=3000)


class PackageInput(Input):
    profile_id: str
    opportunity_id: str
    contact_id: str


class PackageEdit(Input):
    subject: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=20, max_length=5000)

    @field_validator("subject")
    @classmethod
    def safe_subject(cls, value):
        if "\n" in value or "\r" in value:
            raise ValueError("mail headers cannot contain line breaks")
        return value


class Approval(Input):
    package_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class SuppressionInput(Input):
    scope: Literal["email", "company"]
    value: str = Field(min_length=1, max_length=254)
    reason: str = Field(min_length=3, max_length=200)


class BoardInput(Input):
    company_id: str
    provider: Literal["greenhouse", "ashby"]
    board: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,100}$")
    role: Role
