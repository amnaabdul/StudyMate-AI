
def split_text(text, chunk_size=500, overlap=100):
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be between 0 and chunk_size")

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def split_pdf_pages(pdf, chunk_size=500, overlap=100):
    """
    Split PDF pages into chunks and preserve page numbers.
    """
    chunks = []

    for page_number, page in enumerate(pdf, start=1):
        page_text = page.get_text()

        if not page_text.strip():
            continue

        page_chunks = split_text(
            page_text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk in page_chunks:
            chunks.append({
                "text": chunk,
                "page": page_number
            })

    return chunks
