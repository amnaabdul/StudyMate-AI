"""Local, whole-document PDF summarization with Ollama/Qwen."""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"


def _ask_ollama(prompt, max_tokens=550):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": max_tokens},
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def generate_summary(chunks_with_pages, max_chunks=8):
    """Summarize all PDF chunks in batches, then merge partial summaries.

    ``max_chunks`` is the number of chunks per batch (not a document limit).
    Keeps the same interface expected by app.py.
    """
    if not chunks_with_pages:
        return "No text available to summarize."
    if max_chunks < 1:
        raise ValueError("max_chunks must be at least 1")

    partial_summaries = []
    for start in range(0, len(chunks_with_pages), max_chunks):
        batch = chunks_with_pages[start:start + max_chunks]
        context = "\n\n".join(
            f"[PDF Page {item['page']}]\n{item['text']}" for item in batch
        )
        prompt = f"""You are StudyMate AI, a study assistant.
Summarize ONLY the lecture content below. Do not invent information.
Keep important concepts, definitions, and examples. Use concise bullet points.
Mention PDF page numbers when helpful. If the material is a resume or
non-lecture document, describe it accurately rather than inventing a lecture.

Document excerpt:
{context}

Concise partial summary:
"""
        partial_summaries.append(_ask_ollama(prompt))

    # Merge in bounded groups so a long PDF does not overflow the model context.
    # Each level reduces multiple summaries to fewer summaries.
    while len(partial_summaries) > 1:
        merged = []
        group_size = 4
        for start in range(0, len(partial_summaries), group_size):
            group = partial_summaries[start:start + group_size]
            context = "\n\n".join(
                f"[Part {i}]\n{summary}" for i, summary in enumerate(group, 1)
            )
            prompt = f"""Combine these partial document summaries into one concise,
accurate study summary. Use ONLY the provided material; preserve key concepts,
definitions, and useful page references. Remove repetition. Do not add facts.

Partial summaries:
{context}

Combined summary:
"""
            merged.append(_ask_ollama(prompt, max_tokens=750))
        partial_summaries = merged

    return partial_summaries[0]
