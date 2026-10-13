
import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def select_chunks(chunks_with_pages, max_chunks=10):
    """Select chunks from across the PDF."""
    if max_chunks < 1:
        raise ValueError("max_chunks must be positive")
    if not chunks_with_pages:
        return []
    if max_chunks == 1:
        return [chunks_with_pages[0]]

    if len(chunks_with_pages) <= max_chunks:
        return chunks_with_pages

    indices = [
        round(i * (len(chunks_with_pages) - 1) / (max_chunks - 1))
        for i in range(max_chunks)
    ]

    return [chunks_with_pages[i] for i in indices]


def generate_flashcards(chunks_with_pages, num_cards=5):
    """Generate question-and-answer flashcards from a PDF."""

    if not chunks_with_pages:
        raise ValueError("No PDF content available.")

    if not 1 <= num_cards <= 10:
        raise ValueError("Number of flashcards must be between 1 and 10.")

    selected_chunks = select_chunks(chunks_with_pages)

    context = "\n\n".join(
        f"[Page {item['page']}]\n{item['text']}"
        for item in selected_chunks
    )

    prompt = f"""
You are StudyMate AI, an educational flashcard generator.

Create exactly {num_cards} flashcards using ONLY
the study material provided below.

Requirements:
- Each flashcard must contain one clear question.
- Each flashcard must contain one accurate, concise answer.
- Use simple English.
- Cover different important concepts where possible.
- Do not invent information outside the provided material.
- Return ONLY a valid JSON object.
- Do not include Markdown code fences.

Return this JSON structure:

{{
    "flashcards": [
        {{
            "question": "What is ...?",
            "answer": "The explanation..."
        }}
    ]
}}

Study material:
{context}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "num_predict": 1500
            }
        },
        timeout=300
    )

    response.raise_for_status()

    raw_output = response.json()["response"]
    data = json.loads(raw_output)

    if not isinstance(data, dict):
        raise ValueError("Invalid flashcard response.")

    flashcards = data.get("flashcards")

    if not isinstance(flashcards, list):
        raise ValueError("Flashcards are missing from the response.")

    if len(flashcards) != num_cards:
        raise ValueError(
            f"Expected {num_cards} flashcards, "
            f"but received {len(flashcards)}."
        )

    for card in flashcards:
        if not isinstance(card, dict):
            raise ValueError("Invalid flashcard format.")

        question = card.get("question")
        answer = card.get("answer")

        if not isinstance(question, str) or not question.strip():
            raise ValueError("A flashcard question is missing.")

        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("A flashcard answer is missing.")

    return flashcards
