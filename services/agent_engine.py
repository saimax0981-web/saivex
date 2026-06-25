try:
    from brain.intent_detector import detect_intent
except Exception:
    def detect_intent(goal):
        q = goal.lower()
        if "ppt" in q or "presentation" in q:
            return "ppt"
        if "pdf" in q or "report" in q:
            return "pdf"
        if "website" in q or "portfolio" in q:
            return "website"
        if "search" in q or "latest" in q:
            return "search"
        if "code" in q or "python" in q:
            return "code"
        if "image" in q or "photo" in q:
            return "image"
        return "chat"


class SaivexAgent:
    """
    Production Agent OS.
    Compatible with your current app's SaivexAgent(build_agent_tools()).run(goal)
    """

    def __init__(self, tool_callbacks):
        self.tools = tool_callbacks

    def make_plan(self, goal):
        intent = detect_intent(goal)

        q = goal.lower()
        if q.startswith("agent:"):
            q = q.replace("agent:", "", 1).strip()

        if "ppt" in q or "presentation" in q:
            intent = "ppt"
        elif "pdf" in q or "report" in q:
            intent = "pdf"
        elif "website" in q or "portfolio" in q or "landing page" in q:
            intent = "website"
        elif "search" in q or "latest" in q or "current" in q:
            intent = "search"
        elif "code" in q or "python" in q or "debug" in q:
            intent = "code"

        plans = {
            "ppt": [
                "Understand the presentation topic",
                "Research useful information",
                "Create a unique slide outline",
                "Generate PowerPoint",
                "Return download link"
            ],
            "pdf": [
                "Understand the report topic",
                "Research useful information",
                "Create structured sections",
                "Generate PDF",
                "Return download link"
            ],
            "website": [
                "Understand the website goal",
                "Research topic and sections",
                "Generate HTML, CSS, and JavaScript",
                "Package website ZIP",
                "Return preview and download"
            ],
            "search": [
                "Search the internet",
                "Collect useful information",
                "Summarize clearly"
            ],
            "code": [
                "Understand coding task",
                "Run or generate code",
                "Return output and explanation"
            ],
            "image": [
                "Improve visual prompt",
                "Generate image",
                "Return preview"
            ],
            "vision": [
                "Use latest uploaded image",
                "Analyze visual content",
                "Answer the question"
            ],
            "chat": [
                "Understand the request",
                "Use memory and context",
                "Reply naturally"
            ]
        }

        return intent, plans.get(intent, plans["chat"])

    def run(self, goal):
        intent, plan = self.make_plan(goal)

        if intent in self.tools:
            result = self.tools[intent](goal)
        elif "chat" in self.tools:
            result = self.tools["chat"](goal)
        else:
            result = "No compatible tool found."

        plan_text = "🤖 SAIVEX Agent OS Plan:\\n"
        for i, step in enumerate(plan, start=1):
            plan_text += f"{i}. {step}\\n"

        return {
            "intent": intent,
            "plan": plan_text,
            "result": result
        }
