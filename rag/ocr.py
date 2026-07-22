import fitz
import easyocr
import tempfile
import os

reader = easyocr.Reader(
    ['en'],
)

def extract_text_from_scanned_pdf(pdf_path: str):
    doc = fitz.open(pdf_path)

    full_text = ""

    for page in doc:
        pix = page.get_pixmap(dpi=400)
        with tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        ) as temp:
             
            pix.save(temp.name)

            result = reader.readtext(
                temp.name,
                detail=0,
                paragraph=True,
            )

            full_text += "\n".join(result) + "\n"
            os.remove(temp.name)
    return full_text