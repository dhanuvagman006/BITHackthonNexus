from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="Self-Healing Demo")
templates = Jinja2Templates(directory="backend/templates")

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "status": "DEMO ACTIVE"})

@app.get("/crash")
def crash():
    print("[!] Manual crash triggered via index.py")
    os._exit(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
