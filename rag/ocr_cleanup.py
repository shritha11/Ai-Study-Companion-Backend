from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

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
    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    return response.choices[0].message.content