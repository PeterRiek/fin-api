from datetime import date as dt_date, datetime

from pydantic import BaseModel, ConfigDict


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

    id: int
    space_id: int
    user_id: int
    is_owner: bool


# ---------- Transaction ----------

class TransactionCreate(BaseModel):
    space_id: int
    title: str
    description: str | None = None
    date: dt_date


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    space_id: int
    title: str
    description: str | None
    date: dt_date
    created_at: datetime


# ---------- AccountTransaction ----------

class AccountTransactionCreate(BaseModel):
    account_id: int
    transaction_id: int
    amount_requested: float
    amount_paid: float
    is_initial: bool = False


class AccountTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    transaction_id: int
    amount_requested: float
    amount_paid: float
    is_initial: bool
