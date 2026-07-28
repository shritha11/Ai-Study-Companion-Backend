from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

print("API:", repr(os.getenv("NOVA_API_KEY")))
print("BASE:", repr(os.getenv("NOVA_BASE_URL")))
print("MODEL:", repr(os.getenv("NOVA_MODEL")))

client = OpenAI(
    api_key=os.getenv("NOVA_API_KEY"),
    base_url=os.getenv("NOVA_BASE_URL"),
)

response = client.chat.completions.create(
    model=os.getenv("NOVA_MODEL"),
    messages=[
        {
            "role": "user",
            "content": "Say hello!"
        }
    ]
)

print(response.choices[0].message.content)