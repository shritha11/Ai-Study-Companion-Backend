from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()


def clean_ocr_text(text: str):
    prompt = f"""
You are an OCR correction assistant.

The following text was extracted from handwritten notes using OCR.

Correct ONLY OCR mistakes.

Rules:
- Do NOT summarize.
- Do NOT add information.
- Do NOT remove information.
- Preserve headings.
- Preserve bullet points.
- Preserve order.
- Fix spelling mistakes caused by OCR.
- Return ONLY the corrected notes.

OCR TEXT:

{text}
"""
    corrected = ask_llm(
        "",
        prompt,
    )

    return corrected