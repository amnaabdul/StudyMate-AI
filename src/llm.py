
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def generate_answer(question, relevant_chunks):
    context = "\n\n".join(
        f"[Source {index}]\n{result['text']}"
        for index, result in enumerate(relevant_chunks, start=1)
    )

    
    prompt = f"""
You are StudyMate AI, a helpful AI study assistant.

Your task is to answer the student's question using ONLY
the information provided in the context.

Rules:
1. Use only the provided context.
2. Do not invent facts or add unsupported information.
3. If the answer is not found in the context, say:
   "I couldn't find the answer in the uploaded document."
4. Keep the answer clear, concise, and easy to study.
5. Start with a direct answer to the question.
6. Use bullet points only when they improve clarity.
7. Avoid repeating the same information.
8. Cite relevant context chunks using [Source 1],
   [Source 2], or [Source 3].
9. Answer in the same language as the student's question.

Context:
{context}

Student question:
{question}

Answer:
"""


    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        },
        timeout=180
    )

    response.raise_for_status()

    return response.json()["response"]
