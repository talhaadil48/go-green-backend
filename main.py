from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import forms_router
app = FastAPI(title="My App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],            # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],            # Allow all headers
)


app.include_router(forms_router)