import fitz
import docx


def read_pdf(path):

    text = ""

    pdf = fitz.open(path)

    for page in pdf:
        text += page.get_text()

    pdf.close()

    return text


def read_docx(path):

    document = docx.Document(path)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def read_txt(path):

    with open(path, "r", encoding="utf-8") as file:
        return file.read()