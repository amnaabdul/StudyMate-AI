import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def select_representative_chunks(chunks_with_pages, max_chunks=12):
    """Select chunks spread across the PDF while preserving document order."""
    if not chunks_with_pages:
        return []
    count = min(max_chunks, len(chunks_with_pages))
    if count == 1:
        return [chunks_with_pages[0]]
    indices = [(i * (len(chunks_with_pages) - 1)) // (count - 1) for i in range(count)]
    return [chunks_with_pages[index] for index in indices]


def generate_quiz(chunks_with_pages, num_questions=5):
    if not chunks_with_pages:
        raise ValueError("No PDF content available.")
    if not 1 <= num_questions <= 10:
        raise ValueError("Number of questions must be between 1 and 10.")

    selected_chunks = select_representative_chunks(chunks_with_pages)
    context = "\n\n".join(
        f"[Page {item['page']}]\n{item['text']}" for item in selected_chunks
    )

    prompt = f"""You are StudyMate AI, a study quiz generator.

Create exactly {num_questions} multiple-choice questions using ONLY the lecture notes below.
Distribute questions across different topics and pages when the provided context allows.
Do not claim to cover information not included in the provided excerpts.

Requirements:
- Each question must have exactly 4 distinct options and one correct answer.
- Use clear and simple English.
- Do not introduce information outside the lecture notes.
- Return ONLY a valid JSON object, without Markdown fences.

Use this JSON structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Why this answer is correct"
    }}
  ]
}}

correct_answer must be an integer from 0 to 3.

Lecture excerpts:
{context}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.2, "num_predict": 2400},
            },
            timeout=300,
        )
        response.raise_for_status()
        raw_output = response.json()["response"]
        quiz = json.loads(raw_output)
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not connect to Ollama: {exc}") from exc
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"Ollama returned invalid JSON: {exc}") from exc

    if not isinstance(quiz, dict):
        raise ValueError("Invalid quiz response.")
    questions = quiz.get("questions")
    if not isinstance(questions, list) or len(questions) != num_questions:
        received = len(questions) if isinstance(questions, list) else 0
        raise ValueError(f"Expected {num_questions} questions, but received {received}.")

    for item in questions:
        if not isinstance(item, dict):
            raise ValueError("Invalid question format.")
        if not isinstance(item.get("question"), str) or not item["question"].strip():
            raise ValueError("Question text is missing.")
        options = item.get("options")
        if (not isinstance(options, list) or len(options) != 4
                or not all(isinstance(option, str) and option.strip() for option in options)
                or len({option.strip().casefold() for option in options}) != 4):
            raise ValueError("Each question must have four distinct text options.")
        answer = item.get("correct_answer")
        if type(answer) is not int or not 0 <= answer <= 3:
            raise ValueError("Invalid correct answer index.")
        if not isinstance(item.get("explanation"), str) or not item["explanation"].strip():
            raise ValueError("Question explanation is missing.")

    return questions
