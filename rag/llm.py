from ollama import chat
MODEL = "qwen2.5:7b"

def ask_llm(system, user, temperature=0.7):
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system,
            }, 
            {
                "role": "user", 
                "content": user,
            },
        ],
        options={
            "temperature": temperature,
        },
    )

    return response.message.content