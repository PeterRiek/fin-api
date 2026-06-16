from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date as dt_date


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="account"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", secondary="transaction_categories", back_populates="categories"
    )


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    contributions: Mapped[list["Contribution"]] = relationship(
        "Contribution", back_populates="person"
    )


class TransactionCategories(Base):
    __tablename__ = "transaction_categories"

    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"), primary_key=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"), primary_key=True
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    date: Mapped[dt_date] = mapped_column(nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    categories: Mapped[list["Category"]] = relationship(
        "Category", secondary="transaction_categories", back_populates="transactions"
    )
    contributions: Mapped[list["Contribution"]] = relationship(
        "Contribution", back_populates="transaction", cascade="all, delete-orphan"
    )


class Contribution(Base):
    __tablename__ = "contributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"), nullable=False
    )
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id"), nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    amount_paid: Mapped[int] = mapped_column(nullable=False)
    transaction: Mapped["Transaction"] = relationship(
        "Transaction", back_populates="contributions"
    )
    person: Mapped["Person"] = relationship("Person", back_populates="contributions")
