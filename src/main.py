from fastapi import FastAPI


from app.dependencies import get_db
from app.schemas import UserCreate


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

    username = input("Enter username: ")
    email = input("Enter email: ")
    password = input("Enter password: ")


    usercreate = UserCreate(username=username, email=email, password=password)
    user_id = db.insert_user(usercreate).id
    user = db.get_user(user_id)
    if not user: 
        print(f"user with ID {user_id} not found.")
    else:
        print(f"Inserted user: {user.email} with ID: {user.id}")
