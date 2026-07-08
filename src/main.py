from app.dependencies import get_db
from app.schemas import SpaceCreate, SpaceUserCreate, UserCreate


# app = FastAPI()
#
# app.include_router(router)
#
# @app.get("/")
# def health_check():
#     return {"status": "ok"}, 200

# if __name__ == "__main__":
#     print("running")
#     uvicorn.run(app)


if __name__ == "__main__":
    db = get_db()

    user = None

    def create_user(username):
        email = input("Enter email: ")
        password = input("Enter password: ")
        usercreate = UserCreate(username=username, email=email, password=password)
        user = db.insert_user(data=usercreate)
        print("created user", username)
        return user

    username = input("Enter username: ")

    user = db.get_user_by_username(username=username)
    if user is None:
        print("user not found, creating new user", username)
        user = create_user(username)

    print("signed in as", user.username)

    spaces = db.get_spaces_by_user(user.id)
    print("Available spaces:", ",".join([s.name for s in spaces]))
    selected_space = None

    while True:
        prefix = f"({user.username}){f" ({selected_space.name})" if selected_space else ''}"
        selection = input(f"{prefix} Enter 'q' to quit or 'h' for help: ")
        if selection == "q":
            print("quitting")
            break
        if selection == "s":
            spaces = db.get_spaces_by_user(user.id)
            print("Available spaces:", ",".join([s.name for s in spaces]))
            name = input("Select space: ")
            if name not in [s.name for s in spaces]:
                print("space not found")
                continue
            selected_space = next(s for s in spaces if s.name == name)

            
        if selection == "ss":
            print("creating new space")
            name = input("space name: ")
            spacecreate = SpaceCreate(name=name)
            selected_space = db.insert_space(data=spacecreate)
            spaceusercreate = SpaceUserCreate(space_id=selected_space.id, user_id=user.id, is_owner=True)
            db.insert_space_user(data=spaceusercreate)
            print("creaeting space user", spaceusercreate)



