import uvicorn
from fastapi import FastAPI


from app.routes import router


app = FastAPI()

app.include_router(router)

@app.get("/")
def health_check():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    print("running")
    uvicorn.run(app)
