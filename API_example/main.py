from fastapi import FastAPI

app = FastAPI()


@app.post("/addres")
def root():
    return {"message": "Hello World"}