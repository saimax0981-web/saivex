from brain.intent_detector import detect_intent
from brain.planner import plan_text
from brain.suggestion_engine import suggestions_text
from brain.personality import personality_for_intent

def route_message(message):
    intent = detect_intent(message)
    return {
        "intent": intent,
        "plan": plan_text(intent, message),
        "personality": personality_for_intent(intent),
        "suggestions": suggestions_text(intent)
    }

def is_smart_brain_request(message):
    q = message.lower().strip()
    return q.startswith("brain:") or q.startswith("agent:") or q in ["continue", "next", "what next"]

def brain_intro(message):
    info = route_message(message)
    return f"""⚡ Saivex Smart Brain Activated

Intent detected:
{info['intent']}

{info['plan']}
"""
