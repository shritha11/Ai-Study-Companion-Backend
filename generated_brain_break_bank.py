import json
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# 

TOPICS = {
    "entertainment": [
        "Friends Trivia",
        "Marvel",
        "Disney",
        "Harry Potter",
        "Anime",
        "Sitcoms",
    ],

    "technology": [
        "Programming",
        "Flutter",
        "Artificial Intelligence",
        "Apple",
        "Internet",
    ],

    "geography": [
        "Countries",
        "Capitals",
        "Flags",
        "Landmarks",
    ],

    "gaming": [
        "Minecraft",
        "Pokemon",
        "Roblox",
        "Fortnite",
    ],
}

# 

def generate_batch(topic, batch_number):

    prompt = f"""

Every question must be completely different from the others.

Avoid asking about the same character, event, quote or location more than once.

Do not rewrite the same question in different words.

Generate EXACTLY 10 UNIQUE multiple choice trivia questions about "{topic}".

Return ONLY JSON.

Format:

{{
  "questions":[
    {{
      "question":"...",
      "options":[
        "...",
        "...",
        "...",
        "..."
      ],
      "answer":0
    }}
  ]
}}

Rules:

• Exactly 10 questions

• Every question must be unique.

• Mix:
    - Easy
    - Medium
    - Hard

• Make the quiz FUN.

• Include:
    - famous moments
    - fun facts
    - iconic quotes
    - characters
    - locations
    - memes (when applicable)

• Wrong answers should be believable.

• Never repeat a question.

• Return ONLY valid JSON.

"""



    response = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.9,
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    return data["questions"]


# 
def generate_questions(topic):

    all_questions = []
    seen = set()
    batch = 1

    while len(all_questions) < 50:

        try:

            print(f"   Batch {batch}")

            questions = generate_batch(topic, batch)

            for q in questions:

                key = q["question"].strip().lower()

                if key not in seen:

                    seen.add(key)
                    all_questions.append(q)

                    if len(all_questions) == 50:
                        break

            batch += 1

        except Exception as e:
            print("Batch failed:", e)

    category = "General"

    for folder, topics in TOPICS.items():
        if topic in topics:
            category = folder.capitalize()
            break

    return {
        "category": category,
        "challengeType": "quiz",
        "estimatedTime": "3 mins",
        "questions": all_questions,
    }

    all_questions = []

    seen = set()

    for batch in range(1, 6):

        try:

            questions = generate_batch(topic, batch)

            for q in questions:

                key = q["question"].strip().lower()

                if key not in seen:
                    seen.add(key)
                    all_questions.append(q)

        except Exception as e:
            print("Batch failed:", e)

    category = "General" 
    for folder, topics in TOPICS.items(): 
        if topic in topics:
            category = folder.capitalize()
            break
    return { 
        "category": category,
        "questions": all_questions,
        "challengeType": "quiz",
        "estimatedTime": f"{max(2, len(all_questions)//2)} mins",
    }




def save_questions():

    for folder, topics in TOPICS.items():

        os.makedirs(
            f"generated_questions/{folder}",
            exist_ok=True,
        )

        for topic in topics:

            print("\n==============================")
            print(f"Generating {topic}")
            print("==============================")

            data = generate_questions(topic)

            filename = (
                topic.lower()
                .replace(" ", "_")
                + ".json"
            )

            filepath = (
                f"generated_questions/{folder}/{filename}"
            )

            with open(
                filepath,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

            print(f"Saved {filepath}")
            print(f"Questions: {len(data['questions'])}")



if __name__ == "__main__":
    save_questions()