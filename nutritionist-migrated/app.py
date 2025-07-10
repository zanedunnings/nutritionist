from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
import os
from contextlib import contextmanager
from datetime import datetime
import logging
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import routes
from routes.auth import router as auth_router
from routes.meal_plan import router as meal_plan_router
from routes.main import router as main_router
from routes.waitlist import router as waitlist_router
from routes.nutrition import router as nutrition_router

# Import configuration
from config import DATABASE_URL, PROJECT_NAME

# Create the FastAPI app
app = FastAPI(title=PROJECT_NAME)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up database
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import models
from models.user import User
from models.waitlist import WaitlistEmail
from models.meal_plan import MealPlan, Modification

# Create database tables
Base.metadata.create_all(bind=engine)

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Set up templates
templates = Jinja2Templates(directory="templates")
templates.env.globals["url_for"] = lambda name, **params: app.url_path_for(name, **params)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(meal_plan_router, prefix="/api", tags=["meal-plan"])
app.include_router(main_router, prefix="/app", tags=["main"])
app.include_router(waitlist_router, prefix="/api", tags=["waitlist"])
app.include_router(nutrition_router, prefix="/api/nutrition", tags=["nutrition"])

# Root endpoint - serve landing page
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

# Landing page endpoint
@app.get("/landing")
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 