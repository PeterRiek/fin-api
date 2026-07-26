from datetime import date as dt_date, datetime

from pydantic import BaseModel, ConfigDict

from app.models import TransactionType


# ---------- User ----------


class UserCreate(BaseModel):
    username: str
    email: str
    password: str  # plaintext in, hashed before it touches the DB layer


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime
    # password_hash intentionally omitted — never return it to callers


# ---------- Person ----------


class PersonCreate(BaseModel):
    name: str


class PersonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


# ---------- Account ----------


class AccountCreate(BaseModel):
    name: str
    person_id: int


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    person_id: int
    created_at: datetime


# ---------- Space ----------


class SpaceCreate(BaseModel):
    name: str
    description: str | None = None


class SpaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime


# ---------- SpaceUser ----------


class SpaceUserCreate(BaseModel):
    space_id: int
    user_id: int
    is_owner: bool = False


class SpaceUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    space_id: int
    user_id: int
    is_owner: bool


# ---------- Transaction ----------


class TransactionCreate(BaseModel):
    space_id: int
    title: str
    description: str | None = None
    date: dt_date
    type: TransactionType = TransactionType.EXPENSE


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    title: str
    description: str | None
    date: dt_date
    type: TransactionType
    linked_transaction_id: int | None
    created_at: datetime


# ---------- Contribution ----------


class ContributionCreate(BaseModel):
    account_id: int
    transaction_id: int
    real_amount: float
    liability_amount: float


class ContributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    transaction_id: int
    real_amount: float
    liability_amount: float


class ContributionDetailOut(BaseModel):
    account_id: int
    person_name: str
    real_amount: float
    liability_amount: float


# ---------- Account transactions (income / expense / transfer) ----------


class SimpleTransactionCreate(BaseModel):
    space_id: int
    title: str
    description: str | None = None
    date: dt_date
    type: TransactionType = TransactionType.EXPENSE
    amount: float
    category_id: int | None = None


class TransferCreate(BaseModel):
    space_id: int
    to_account_id: int
    amount: float
    date: dt_date
    title: str
    description: str | None = None
    affects_balance: bool = False


class TransferOut(BaseModel):
    out_transaction: TransactionOut
    in_transaction: TransactionOut


class AccountBalanceOut(BaseModel):
    account_id: int
    balance: float


# ---------- PersonSpace ----------


class PersonSpaceCreate(BaseModel):
    person_id: int
    space_id: int


class PersonSpaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    person_id: int
    space_id: int


# ---------- Category ----------


class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


# ---------- TransactionCategory ----------


class TransactionCategoryCreate(BaseModel):
    transaction_id: int
    category_id: int


class TransactionCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transaction_id: int
    category_id: int


# --------- Authentication ----------


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --------- Composite / enriched views ----------


class TransactionDetailOut(BaseModel):
    id: int
    space_id: int
    title: str
    description: str | None
    date: dt_date
    type: TransactionType
    linked_transaction_id: int | None
    created_at: datetime
    contributions: list[ContributionDetailOut]
    categories: list[CategoryOut]


class PersonBalanceOut(BaseModel):
    person_id: int
    name: str
    net_balance: float


class PersonSummaryOut(BaseModel):
    person_id: int
    name: str
    net_balance: float
    accounts: list[AccountOut]
    transaction_count: int


class SpaceOverviewOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    users: list[UserOut]
    persons: list[PersonOut]
    transaction_count: int
    recent_transactions: list[TransactionDetailOut]


class SpaceSummaryOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    member_count: int
    transaction_count: int
