import os
import uuid
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def create_pdf(title, content, output_folder="static/generated"):
    os.makedirs(output_folder, exist_ok=True)
    filename = f"saivex_report_{uuid.uuid4().hex[:8]}.pdf"
    path = os.path.join(output_folder, filename)
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - 70
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, title[:80])
    y -= 35
    c.setFont("Helvetica", 11)
    for line in content.split("\n"):
        words = line.split()
        current = ""
        for word in words:
            if len(current + " " + word) > 90:
                c.drawString(50, y, current)
                y -= 18
                current = word
                if y < 60:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y = height - 60
            else:
                current += " " + word
        if current.strip():
            c.drawString(50, y, current.strip())
            y -= 18
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 60
    c.save()
    return path
