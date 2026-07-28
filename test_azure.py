from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("NOVA_API_KEY"),
    base_url=os.getenv("NOVA_BASE_URL"),
    MODEL=os.getenv("NOVA_MODEL"),
)

print("Endpoint:", os.getenv("AZURE_OPENAI_ENDPOINT"))
print("Deployment:", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))

response = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    messages=[
        {
            "role": "user",
            "content": "Say hello"
        }
    ],
)

print(response.choices[0].message.content)