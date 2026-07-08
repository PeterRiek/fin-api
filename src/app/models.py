from datetime import date as dt_date, datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    space_links: Mapped[list["SpaceUser"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class SpaceUser(Base):
    __tablename__ = "space_users"
    __table_args__ = (UniqueConstraint("space_id", "user_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    space_id: Mapped[int] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_owner: Mapped[bool] = mapped_column(nullable=False, default=False)

    space: Mapped["Space"] = relationship(back_populates="user_links")
    user: Mapped["User"] = relationship(back_populates="space_links")


class Space(Base):
    __tablename__ = "spaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    user_links: Mapped[list["SpaceUser"]] = relationship(
        back_populates="space", cascade="all, delete-orphan"
    )
    person_links: Mapped[list["PersonSpace"]] = relationship(
        back_populates="space", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="space", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    space_id: Mapped[int] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date: Mapped[dt_date] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    space: Mapped["Space"] = relationship(back_populates="transactions")
    account_links: Mapped[list["AccountTransaction"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )


class AccountTransaction(Base):
    __tablename__ = "account_transactions"

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), primary_key=True
    )
    amount_requested: Mapped[float] = mapped_column(nullable=False)
    amount_paid: Mapped[float] = mapped_column(nullable=False)
    is_initial: Mapped[bool] = mapped_column(nullable=False, default=False)

    account: Mapped["Account"] = relationship(back_populates="transaction_links")
    transaction: Mapped["Transaction"] = relationship(back_populates="account_links")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    person: Mapped["Person"] = relationship(back_populates="accounts")
    transaction_links: Mapped[list["AccountTransaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    space_links: Mapped[list["PersonSpace"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )


class PersonSpace(Base):
    __tablename__ = "person_spaces"

    __table_args__ = (UniqueConstraint("space_id", "person_id"),)
    space_id: Mapped[int] = mapped_column(
        ForeignKey("spaces.id", ondelete="CASCADE"), primary_key=True
    )
    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True
    )
    space: Mapped["Space"] = relationship(back_populates="person_links")
    person: Mapped["Person"] = relationship(back_populates="space_links")
