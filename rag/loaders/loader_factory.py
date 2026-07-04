import os
from rag.loaders.pdf_loader import extract_text_from_pdf
from rag.loaders.docx_loader import extract_text_from_docx
from rag.loaders.pptx_loader import extract_text_from_pptx
from rag.loaders.txt_loader import extract_text_from_txt
from rag.loaders.md_loader import extract_text_from_md

def extract_text(path: str):
    extension = os.path.splitext(path)[1].lower()
    if extension == ".pdf":
        return extract_text_from_pdf(path)
    elif extension == ".docx":
        return extract_text_from_docx(path)
    elif extension == ".pptx":
        return extract_text_from_pptx(path)
    elif extension == ".txt":
        return extract_text_from_txt(path)
    elif extension == ".md":
        return extract_text_from_md(path)
    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )
