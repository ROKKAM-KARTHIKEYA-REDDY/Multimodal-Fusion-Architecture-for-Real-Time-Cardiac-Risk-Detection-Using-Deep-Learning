from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from .auth import get_current_user_optional, get_current_user
from .database import init_db, get_db
from .models import Submission
from .routers import auth_routes, upload_routes
from .routers import ppg_routes
from .routers import report_routes
from .routers import profile_routes
from .routers import heart_routes
from .routers import fusion_routes
from .routers import chatbot_routes

# Load .env from project root
load_dotenv()

app = FastAPI(title="Heart Health")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="backend/templates")

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
app.include_router(upload_routes.router, prefix="/ecg", tags=["ecg"])
app.include_router(report_routes.router, prefix="/ecg", tags=["report"])
app.include_router(profile_routes.router, tags=["profile"])
app.include_router(ppg_routes.router, prefix="/ppg", tags=["ppg"])
app.include_router(heart_routes.router, tags=["heart"]) 
app.include_router(fusion_routes.router, tags=["fusion"]) 
app.include_router(chatbot_routes.router, tags=["chatbot"])

@app.on_event("startup")
async def on_startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user=Depends(get_current_user_optional)):
    if user:
        return RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "user": None})

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, user=Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})

@app.get("/upload", response_class=HTMLResponse)
async def choose_upload(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("upload_choice.html", {"request": request, "user": user})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    subs = db.query(Submission).filter(Submission.user_id == user.id).order_by(Submission.created_at.desc()).all()

    def is_normal(label: str | None) -> bool:
        if not label:
            return False
        try:
            idx = int(label)
            return idx == 3
        except Exception:
            return "normal" in label.lower()

    total = len(subs)
    normal_cnt = sum(1 for s in subs if is_normal(s.predicted_label))
    abnormal_cnt = total - normal_cnt

    def infer_test_type(s: Submission) -> str:
        try:
            if getattr(s, "test_type", None):
                return s.test_type  # type: ignore[attr-defined]
        except Exception:
            pass
        name = (s.file_name or "").lower()
        if name.endswith(".csv") or name.endswith(".npy"):
            return "ECG"
        # Default to ECG for legacy uploads
        return "ECG"

    subs_view = [
        {
            "id": s.id,
            "created_at": s.created_at,
            "file_name": s.file_name,
            "test_type": infer_test_type(s),
            "predicted_score": s.predicted_score,
            "result": ("Normal" if is_normal(s.predicted_label) else "Abnormal"),
        }
        for s in subs
    ]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "submissions": subs_view,
            "stats": {"total": total, "normal": normal_cnt, "abnormal": abnormal_cnt},
        },
    )
