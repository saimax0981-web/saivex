def suggestions_for(intent):
    data = {
        "ppt": ["Create a PDF from this topic", "Generate images for slides", "Make it more professional"],
        "pdf": ["Create PPT from this PDF", "Summarize shorter", "Make it student-friendly"],
        "website": ["Improve design", "Add animations", "Make it mobile-first"],
        "search": ["Create report from results", "Make PPT from this", "Search deeper"],
        "image": ["Create another version", "Make it 16:9 wallpaper", "Create Instagram poster"],
        "vision": ["Extract text", "Explain simply", "Create notes from image"],
        "code": ["Fix the error", "Explain code", "Optimize code"],
        "chat": ["Create PPT", "Create PDF", "Search internet"],
        "continue": ["Continue coding", "Move to next phase", "Create a roadmap"]
    }
    return data.get(intent, data["chat"])

def suggestions_text(intent):
    suggestions = suggestions_for(intent)
    text = "\n\nSuggestions:\n"
    for item in suggestions:
        text += f"• {item}\n"
    return text
