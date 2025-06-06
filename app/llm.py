# app/llm.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
from groq import Groq
from .dependencies import get_db
from .models import User
from dotenv import load_dotenv
from .dependencies import get_current_user
load_dotenv()
router = APIRouter()

@router.post("/llm/suggest-subtasks")
def suggest_subtasks(goal: str, current_user: User = Depends(get_current_user)):
    prompt = (
        f"Break down this goal into a JSON array, each item with 'title', 'weight' (1-5), "
        f"and 'deadline_days' (days from now).\n"
        f"Goal: {goal}\n\n"
        "Example output:\n"
        '[{"title": "First step", "weight": 2, "deadline_days": 2}]\n'
    )
    try:
        client = Groq()  # Assumes GROQ_API_KEY set as env var
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1,
            max_completion_tokens=512,
            top_p=1,
            stream=False,
        )
        text_response = completion.choices[0].message.content.strip()
        import json
        # Try to extract JSON from the model output (handle possible non-JSON text)
        import re
        match = re.search(r'$$.*$$', text_response, re.DOTALL)
        if match:
            json_str = match.group(0)
            suggestions = json.loads(json_str)
        else:
            # Fallback: Try loading entire response
            suggestions = json.loads(text_response)
        return {"suggested": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")