from datetime import date

from app.dependencies import get_db
from app.database import Database
from app.schemas import (
    AccountCreate,
    AccountTransactionCreate,
    PersonCreate,
    PersonSpaceCreate,
    SpaceCreate,
    SpaceUserCreate,
    TransactionCreate,
    UserCreate,
)


HELP_TEXT = """
Commands:
  s   select a space
  ss  create a new space
  p   list persons in the current space
  pp  add a new person to the current space
  t   list transactions in the current space
  tt  add a new transaction to the current space
  h   show this help
  q   quit
"""


def create_user(db: Database, username: str):
    email = input("Enter email: ")
    password = input("Enter password: ")
    usercreate = UserCreate(username=username, email=email, password=password)
    user = db.insert_user(data=usercreate)
    print("created user", username)
    return user


def sign_in(db: Database):
    username = input("Enter username: ")
    user = db.get_user_by_username(username=username)
    if user is None:
        print("user not found, creating new user", username)
        user = create_user(db, username)
    print("signed in as", user.username)
    return user


def select_space(db: Database, user):
    spaces = db.get_spaces_by_user(user.id)
    if not spaces:
        print("no spaces available, create one with 'ss'")
        return None
    print("Available spaces:", ", ".join(s.name for s in spaces))
    name = input("Select space: ")
    space = next((s for s in spaces if s.name == name), None)
    if space is None:
        print("space not found")
    return space


def create_space(db: Database, user):
    name = input("space name: ")
    space = db.insert_space(data=SpaceCreate(name=name))
    db.insert_space_user(
        data=SpaceUserCreate(space_id=space.id, user_id=user.id, is_owner=True)
    )
    print("created space", space.name)
    return space


def list_persons(db: Database, space):
    persons = db.get_persons_by_space(space.id)
    if not persons:
        print("no persons in this space yet, add one with 'pp'")
        return persons
    print("Persons in", space.name, ":", ", ".join(p.name for p in persons))
    return persons


def add_person(db: Database, space):
    name = input("person name: ")
    person = db.insert_person(data=PersonCreate(name=name))
    db.insert_person_space(
        data=PersonSpaceCreate(person_id=person.id, space_id=space.id)
    )
    print("added", person.name, "to", space.name)
    return person


def get_or_create_account(db: Database, person):
    accounts = db.get_accounts_by_person(person.id)
    if accounts:
        return accounts[0]
    account = db.insert_account(
        data=AccountCreate(name=f"{person.name}'s account", person_id=person.id)
    )
    return account


def create_transaction(db: Database, space):
    persons = list_persons(db, space)
    if len(persons) < 2:
        print("need at least 2 persons in the space to record a transaction")
        return

    title = input("title: ")
    description = input("description (optional): ") or None
    date_input = input("date (YYYY-MM-DD, blank for today): ")
    tx_date = date.fromisoformat(date_input) if date_input else date.today()

    print("Participants:", ", ".join(p.name for p in persons))
    participant_names = input("Who participated? (comma separated, blank for all): ")
    if participant_names.strip():
        wanted = {n.strip() for n in participant_names.split(",")}
        participants = [p for p in persons if p.name in wanted]
    else:
        participants = persons
    if len(participants) < 2:
        print("need at least 2 participants")
        return

    payer_name = input("Who paid? ")
    payer = next((p for p in participants if p.name == payer_name), None)
    if payer is None:
        print("payer must be one of the participants")
        return

    total = float(input("total amount: "))
    share = round(total / len(participants), 2)

    transaction = db.insert_transaction(
        data=TransactionCreate(
            space_id=space.id, title=title, description=description, date=tx_date
        )
    )

    for person in participants:
        account = get_or_create_account(db, person)
        is_payer = person.id == payer.id
        db.insert_account_transaction(
            data=AccountTransactionCreate(
                account_id=account.id,
                transaction_id=transaction.id,
                amount_requested=share,
                amount_paid=total if is_payer else 0.0,
                is_initial=is_payer,
            )
        )

    print(f"recorded '{title}' ({total:.2f}) paid by {payer.name}, split {len(participants)} ways")


def list_transactions(db: Database, space):
    transactions = db.get_transactions_by_space(space.id)
    if not transactions:
        print("no transactions in this space yet, add one with 'tt'")
        return

    persons_by_account = {}
    for person in db.get_persons_by_space(space.id):
        for account in db.get_accounts_by_person(person.id):
            persons_by_account[account.id] = person.name

    for tx in sorted(transactions, key=lambda t: t.date):
        print(f"[{tx.date}] {tx.title}" + (f" - {tx.description}" if tx.description else ""))
        for at in db.get_account_transactions_by_transaction(tx.id):
            who = persons_by_account.get(at.account_id, f"account {at.account_id}")
            paid_marker = " (paid)" if at.is_initial else ""
            print(f"    {who}: owes {at.amount_requested:.2f}, paid {at.amount_paid:.2f}{paid_marker}")


if __name__ == "__main__":
    db = get_db()

    user = sign_in(db)
    selected_space = None

    print(HELP_TEXT)

    while True:
        prefix = f"({user.username})" + (f" ({selected_space.name})" if selected_space else "")
        selection = input(f"{prefix} Enter a command ('h' for help): ").strip()

        if selection == "q":
            print("quitting")
            break
        elif selection == "h":
            print(HELP_TEXT)
        elif selection == "s":
            space = select_space(db, user)
            if space is not None:
                selected_space = space
        elif selection == "ss":
            selected_space = create_space(db, user)
        elif selection in ("p", "pp", "t", "tt") and selected_space is None:
            print("select or create a space first ('s' / 'ss')")
        elif selection == "p":
            list_persons(db, selected_space)
        elif selection == "pp":
            add_person(db, selected_space)
        elif selection == "t":
            list_transactions(db, selected_space)
        elif selection == "tt":
            create_transaction(db, selected_space)
        else:
            print("unknown command, enter 'h' for help")
