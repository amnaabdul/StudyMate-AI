# StudyMate AI

A local PDF study assistant that turns lecture notes into summaries, searchable study material, quizzes, and flashcards. Built with Python and Streamlit, StudyMate AI uses Ollama with `qwen2.5:3b` for AI generation and SQLite to preserve study progress.

## Features

- **PDF reading:** upload one PDF, extract selectable text, and inspect chunks with actual PDF page numbers.
- **Lecture summaries:** summarize the document in batches and download the summary as text.
- **Semantic search and questions:** generate text embeddings, retrieve relevant passages, and ask AI questions with source excerpts and page numbers.
- **Multiple-choice quizzes:** generate 3, 5, or 10 questions, receive scores and explanations, retry the same questions, and download results.
- **Study progress:** save quiz attempts in SQLite and view attempt history, best and latest scores, and a progress chart.
- **Flashcards:** generate 3, 5, or 10 question-and-answer cards, reveal answers, navigate cards, and track learned/unlearned progress.
- **Saved decks:** reload the latest saved flashcard deck for a PDF without generating it again. Decks and learning progress survive application restarts.

## Technology stack

| Component | Technology |
| --- | --- |
| Application and interface | Python 3.12, Streamlit |
| PDF extraction | PyMuPDF |
| Text embeddings | sentence-transformers, `all-MiniLM-L6-v2` |
| Similarity search | NumPy |
| Local AI generation | Ollama, `qwen2.5:3b` |
| Ollama API client | Requests |
| Persistent storage | SQLite (Python standard library) |
| Progress tables and charts | pandas, Streamlit |
| Automated tests | unittest, mocks, Streamlit AppTest |

## Project structure

```text
StudyMate-AI/
├── app.py                        # Streamlit interface and session state
├── src/
│   ├── database.py               # Quiz history, saved decks, learned progress
│   ├── embeddings.py             # Load the embedding model and encode text
│   ├── flashcards.py             # Generate and validate flashcards
│   ├── llm.py                    # Answer questions using retrieved passages
│   ├── quiz_generator.py         # Generate and validate quiz questions
│   ├── semantic_search.py        # Rank chunks by embedding similarity
│   ├── summarizer.py             # Batch summaries and merge results
│   └── text_chunker.py           # Split text while retaining PDF page numbers
├── tests/
│   └── test_stabilization.py      # Storage, content, and UI regression tests
├── .github/workflows/tests.yml   # Automated CI tests
├── .streamlit/config.toml        # Loopback binding; usage statistics disabled
├── .gitignore
├── requirements.txt
└── README.md
```

`studymate.db` is created automatically in the project root when the application starts. It contains local user data and is excluded from Git.

## Windows installation

### 1. Install prerequisites

Install **64-bit Python 3.12** from [python.org](https://www.python.org/downloads/windows/). Install the Python launcher if offered. Python 3.12 is the version used for local verification and CI.

Download this repository as a ZIP and extract it, or clone it using Git once it has been published. Open PowerShell in the project folder containing `app.py` and `requirements.txt`. All commands below run from that folder.

Check Python:

```powershell
py -3.12 --version
```

### 2. Create a virtual environment

```powershell
py -3.12 -m venv .venv
```

Optional activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the explicit Python paths below; no execution-policy change is required. If this project already has a working `.venv`, reuse it.

### 3. Install Python dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The requirements list only direct project dependencies, pinned to the locally verified versions. Their dependencies, including PyTorch, are installed automatically. SQLite and unittest need no separate installation. Allow time and disk space for the machine-learning packages.

### 4. Install Ollama and download Qwen

Download and install [Ollama for Windows](https://ollama.com/download/windows), then reopen PowerShell so the `ollama` command is available. The Windows application normally starts the local server in the background; see the [official Windows guide](https://docs.ollama.com/windows).

```powershell
ollama --version
ollama pull qwen2.5:3b
ollama list
```

If the server is not already running, start it in a separate terminal and leave that terminal open:

```powershell
ollama serve
```

The app calls `http://localhost:11434/api/generate`. A port-in-use message from `ollama serve` can mean Ollama is already running. The [Ollama CLI reference](https://docs.ollama.com/cli) describes model and server commands.

### 5. Launch StudyMate AI

From the project root:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open `http://127.0.0.1:8501` in your browser. Stop the app with **Ctrl+C** in its terminal.

## How to use it

1. Upload a PDF containing selectable text and inspect its extracted text.
2. Generate a summary, flashcard deck, or quiz using the relevant button.
3. Review flashcards and mark cards as learned or unlearned. Re-upload the same PDF after a restart and choose **Load Saved Flashcards** to resume.
4. Answer every quiz question before submitting. View explanations, download results, or retry. The progress tracker shows saved attempts for the uploaded filename.
5. Select **Generate Embeddings**, enter a question, and select **Search** to retrieve passages and generate an answer.

The first embedding-model load downloads `sentence-transformers/all-MiniLM-L6-v2` from Hugging Face. Subsequent use can reuse the local model cache. If embedding generation fails, check internet access for the initial download and available memory. If AI generation fails, check that Ollama is running and `ollama list` includes `qwen2.5:3b`.

## Automated tests

Run from the project root:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Optional syntax check:

```powershell
.\.venv\Scripts\python.exe -m compileall -q app.py src tests
```

The 10 stabilization tests cover SQLite persistence and validation, real PDF page numbers, duplicate-text retrieval, mocked AI responses, application startup, saved-deck loading, learned progress, quiz submission deduplication, and retry state. Tests use temporary databases and synthetic PDFs. They do not need Ollama running or downloaded AI models.

GitHub Actions runs syntax checks and the tests on pushes and pull requests using Windows and Python 3.12. Model downloads are disabled during CI tests. CI installs Python dependencies but does not install Ollama.

## Local processing and privacy

PDF extraction and embeddings run on your computer. PDF excerpts used for summaries, quizzes, flashcards, and answers are sent to **local Ollama**. The application code does not send document content to a hosted AI service or require an API key.

Initial Python-package installation and model downloads require internet access. Model libraries may check their hosting service for cached-model updates; local inference is not a guarantee that every dependency makes zero network requests. Streamlit usage statistics are disabled in the supplied configuration, and the app binds to `127.0.0.1` by default.

Uploaded PDFs are processed in memory; the app does not deliberately save their original files to the project folder. Quiz filenames, scores, saved flashcard questions and answers, and learning progress are stored in **unencrypted** `studymate.db`. Browser downloads may also contain study content. Protect these files like the original documents.

The `.gitignore` excludes databases and SQLite sidecars, PDFs, common document formats, local study-material/output folders, generated result files, secrets, and virtual environments. Keep other private notes inside an ignored folder such as `study_materials/`. Ignore rules cannot remove files already tracked by Git; review the staged files before publishing.

## Current limitations

- Scanned or image-only PDFs are unsupported without OCR. Complex layouts and tables may extract imperfectly.
- AI summaries, questions, flashcards, and answer keys can contain errors. Check important information against the original PDF. Displayed sources are retrieved excerpts, not verified citations.
- Quiz and flashcard generation sample excerpts from across the PDF; they may not cover every topic. Summaries process all chunks in batches but still compress information.
- Long PDFs and AI generation may be slow or exceed request timeouts, depending on available memory and hardware.
- The application handles one uploaded PDF at a time. Embeddings, summaries, and the current quiz are held in session state rather than saved across restarts.
- Quiz history is grouped by filename, so unrelated PDFs with identical names share history. Flashcard decks are identified by PDF content hash; generating a new deck replaces the saved deck for that PDF. Learning progress is keyed by question text.
- The app is intended for personal local use. It has no user accounts, access controls, or database encryption.
- Direct dependency versions are pinned, but transitive dependencies are not fully locked. Local verification covers Windows and Python 3.12.

## Future improvements

These are planned possibilities, not current features:

- OCR for scanned PDFs and improved extraction of tables and complex layouts.
- Multiple-document study sessions and persistent embedding caches.
- Quiz history identified by document content rather than filename.
- Multiple saved flashcard decks per PDF and spaced repetition.
- More resilient AI-response validation, retries, and generation progress feedback.
- Additional export formats, accessibility checks, and broader integration tests.
