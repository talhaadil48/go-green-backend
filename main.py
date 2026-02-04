from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api import forms_router, login_router ,email_router

app = FastAPI(title="My App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Include routers and protect with token
app.include_router(forms_router)
app.include_router(login_router)  # leave login public
app.include_router(email_router)
