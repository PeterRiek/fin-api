from pydantic import BaseModel, ConfigDict
from datetime import date


# --- Creation Schemas ---


class ContributionCreate(BaseModel):
    person: str
    amount: int
    amount_paid: int


class TransactionCreate(BaseModel):
    title: str
    description: str | None = None
    date: date
    amount: int
    account: str
    categories: list[str]
    contributions: list[ContributionCreate]


class NameSchema(BaseModel):
    name: str


# --- Response Schemas ---


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class PersonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ContributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: int
    amount_paid: int
    person: PersonResponse


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    transaction_date: date
    amount: int
    account: AccountResponse
    categories: list[CategoryResponse]
    contributions: list[ContributionResponse]
