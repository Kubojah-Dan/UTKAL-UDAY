import json
import os
from groq import AsyncGroq

# Initialize groq client (make sure GROQ_API_KEY is in your .env)
groq_client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY", ""))

async def save_to_mongodb_bulk(questions: list, grade: int, subject: str, topic: str):
    \"\"\"
    Placeholder for the actual MongoDB saving function.
    You will need to import your database configuration.
    \"\"\"
    print(f"Saving {len(questions)} questions for Grade {grade} {subject}: {topic}")
    pass

def parse_and_validate(response):
    \"\"\"
    Extracts JSON array from the Groq API response.
    \"\"\"
    try:
        content = response.choices[0].message.content
        # Find json block if it exists
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        return json.loads(content)
    except Exception as e:
        print(f"Failed to parse Groq response: {str(e)}")
        return []

async def batch_generate_questions(grade: int, subject: str, topic: str, count: int = 100):
    \"\"\"
    Generates high-quality conceptual questions using Groq.
    \"\"\"
    prompt = f\"\"\"Generate {count} varied questions for Grade {grade} {subject} on topic: {topic}.
    Include: MCQ (40%), Fill-in-blanks (30%), True/False (20%), Short answer (10%).
    Format strictly as a JSON array. Each question object should have these keys: 
    {{ "question", "type", "options", "answer", "difficulty(1-5)", "explanation" }}
    For Non-MCQ, set options to an empty list or null.
    \"\"\"
    
    try:
        response = await groq_client.chat.completions.create(
            model="llama3-70b-8192", 
            messages=[
                {"role": "system", "content": "You are an expert educator strictly outputting JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"} # Optional if strictly json needed, but array isn't technically an object.
        )
        questions = parse_and_validate(response)
        await save_to_mongodb_bulk(questions, grade, subject, topic)
        return questions
    except Exception as e:
        print(f"Error calling Groq API: {str(e)}")
        return []
