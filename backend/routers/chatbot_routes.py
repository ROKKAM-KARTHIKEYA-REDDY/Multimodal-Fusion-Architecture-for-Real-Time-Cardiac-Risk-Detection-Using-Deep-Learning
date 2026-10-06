from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import random

from ..auth import get_current_user_optional
from ..database import get_db
from ..models import Submission, User

router = APIRouter()

HEALTH_TIPS = [
    "Maintain a healthy weight. Extra weight puts extra strain on your heart.",
    "Exercise for at least 150 minutes per week. Walking, swimming, or cycling are great options.",
    "Follow a balanced diet. Focus on fruits, vegetables, whole grains, and lean proteins.",
    "Avoid tobacco in all forms. Smoking is a major risk factor for heart disease.",
    "Monitor your blood pressure and cholesterol levels regularly.",
    "Reduce sodium intake to help maintain healthy blood pressure.",
    "Manage stress through techniques like meditation, yoga, or deep breathing exercises.",
    "Get enough quality sleep. 7-9 hours is recommended for most adults.",
    "Stay hydrated. Drink plenty of water throughout the day.",
    "Limit alcohol consumption to moderate levels."
]

@router.get("/chatbot/query")
async def chatbot_query(query: str, user: Optional[User] = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    query = query.lower().strip()
    
    # 1. Health Tips
    if any(word in query for word in ["tip", "health", "advice", "suggest"]):
        return {"response": f"💡 **Heart Health Tip:** {random.choice(HEALTH_TIPS)}"}
    
    # 2. Report Summary
    if "report" in query or "result" in query or "check" in query:
        if not user:
            return {"response": "Please [login](/auth/login) to view your latest health reports."}
        
        last_sub = db.query(Submission).filter(Submission.user_id == user.id).order_by(Submission.created_at.desc()).first()
        if not last_sub:
            return {"response": "You haven't submitted any tests yet. Try [uploading](/upload) your data first!"}
        
        result_text = "Normal"
        try:
            if last_sub.predicted_label:
                if isinstance(last_sub.predicted_label, str) and "normal" in last_sub.predicted_label.lower():
                    result_text = "Normal"
                else:
                    idx = int(last_sub.predicted_label)
                    result_text = "Normal" if idx == 3 else "Abnormal"
        except Exception:
            result_text = "Abnormal"
            
        return {
            "response": (
                f"📊 **Latest Report Summary**\n"
                f"Date: {last_sub.created_at.strftime('%Y-%m-%d')}\n"
                f"Test Type: {getattr(last_sub, 'test_type', 'ECG')}\n"
                f"Result: **{result_text}**\n\n"
                f"You can view the full details in your [Dashboard](/dashboard)."
            )
        }

    # 3. Greetings
    if any(word in query for word in ["hi", "hello", "hey", "start"]):
        name = user.full_name or "there" if user else "there"
        return {
            "response": (
                f"Hello {name}! 👋 I'm your Heart Health Assistant.\n\n"
                "I can help you with:\n"
                "• Health tips (Type 'tips')\n"
                "• Your latest results (Type 'report')\n\n"
                "How can I help you today?"
            )
        }

    # 4. Fallback
    return {
        "response": "I didn't quite catch that. Try asking for 'tips' or your 'latest report'!"
    }
