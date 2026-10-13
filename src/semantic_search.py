
import numpy as np


def search_similar_chunks(
    question,
    chunks,
    embeddings,
    model,
    top_k=3
):
    # Convert the question into an embedding
    question_embedding = model.encode(
        question,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # Compare the question with all text chunks
    similarities = np.dot(
        embeddings,
        question_embedding
    )

    # Get the most relevant chunks
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []

    for index in top_indices:
        results.append({
            "text": chunks[index],
            "index": int(index),
            "score": float(similarities[index])
        })

    return results
