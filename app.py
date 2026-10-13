import streamlit as st

import pymupdf

import pandas as pd

import hashlib

from src.text_chunker import split_pdf_pages

from src.embeddings import load_embedding_model, create_embeddings

from src.semantic_search import search_similar_chunks

from src.llm import generate_answer

from src.summarizer import generate_summary

from src.quiz_generator import generate_quiz

from src.flashcards import generate_flashcards

from src.database import (

    init_database, save_quiz_attempt, get_quiz_attempts,

    save_flashcard_progress, get_learned_flashcards,
    save_flashcards, get_saved_flashcards,

)

@st.cache_resource

def get_model():

    return load_embedding_model()

st.set_page_config(page_title="StudyMate AI", page_icon="🎓", layout="wide")



# Initialize persistent quiz storage on every app launch (idempotent).

try:
    init_database()
except Exception as error:
    st.error(f"Could not initialize local study storage: {error}")
    st.stop()

st.markdown("""

<style>

    .stApp { background-color: #0f0b1e; color: #f3e8ff; }

    h1 { color: #c4b5fd !important; }

    .stTextArea textarea {

        background-color: #211a36 !important;

        color: #ffffff !important;

        border: 1px solid #8b5cf6 !important;

    }

    .stTextArea textarea:focus { border-color: #c4b5fd !important; }

    .stTextInput input {

        background-color: #211a36 !important;

        color: #ffffff !important;

        border: 1px solid #8b5cf6 !important;

    }

    .stTextInput label { color: #e9d5ff !important; }

    .stButton button, .stDownloadButton button, .stFormSubmitButton button {

        background-color: #7c3aed !important;

        color: #ffffff !important;

        border: none !important;

        font-weight: 600 !important;

    }

    .stButton button:hover, .stDownloadButton button:hover,

    .stFormSubmitButton button:hover {

        background-color: #6d28d9 !important;

        color: #ffffff !important;

    }

    .stTextInput input::placeholder {

        color: #a78bfa !important;

        opacity: 0.85 !important;

    }

    /* Quiz controls: readable text on the dark purple background */

    .stRadio label, .stRadio label p,

    .stRadio [role="radiogroup"] label,

    .stRadio [role="radiogroup"] p,

    .stSelectbox label, .stSelectbox label p {

        color: #f3e8ff !important;

    }

    /* Keep select menu text legible against its light input surface */

    .stSelectbox [data-baseweb="select"] > div {

        background-color: #211a36 !important;

        color: #f3e8ff !important;

        border-color: #8b5cf6 !important;

    }

    .stSelectbox [data-baseweb="select"] span,

    .stSelectbox [data-baseweb="select"] svg {

        color: #f3e8ff !important;

        fill: #f3e8ff !important;

    }

    /* Feedback alerts: maintain contrast for success, error, and info */

    [data-testid="stAlert"] p,

    [data-testid="stAlert"] li {

        color: #f3e8ff !important;

    }

</style>

""", unsafe_allow_html=True)

st.title("🎓 StudyMate AI")

st.subheader("Your Personal AI Study Assistant")

st.write(

    "Upload your lecture notes, ask questions, "

    "generate summaries, and prepare for exams with AI."

)

st.success("Welcome! Your AI learning journey starts here 💜")

st.divider()

st.header("📚 Upload Your Study Materials")

uploaded_file = st.file_uploader("Choose a PDF lecture file", type=["pdf"])

if uploaded_file is not None:

    st.success(f"File uploaded successfully: {uploaded_file.name}")

    st.write(f"File size: {uploaded_file.size / 1024:.1f} KB")

    try:

        pdf_bytes = uploaded_file.getvalue()

        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as pdf:

            st.info(f"📄 Total pages: {len(pdf)}")

            has_text = any(page.get_text().strip() for page in pdf)

            extracted_text = "".join(

                f"\n\n--- Page {page_number} ---\n{page.get_text()}"

                for page_number, page in enumerate(pdf, start=1)

            )

            chunks_with_pages = split_pdf_pages(pdf, chunk_size=500, overlap=100)

        st.subheader("📝 Extracted Text")

        if has_text:

            st.text_area("Content of your PDF", value=extracted_text, height=350)

        else:

            st.warning("No selectable text was found. This PDF may contain scanned images.")

        if chunks_with_pages:

            chunks = [item["text"] for item in chunks_with_pages]

            pdf_id = hashlib.sha256(pdf_bytes).hexdigest()

            file_id = (uploaded_file.name, pdf_id)

            if st.session_state.get("file_id") != file_id:

                st.session_state.file_id = file_id

                st.session_state.embeddings = None

                st.session_state.summary = None

                st.session_state.quiz = None

                st.session_state.quiz_result = None

                st.session_state.flashcards = None

                st.session_state.flashcard_index = 0

                st.session_state.show_flashcard_answer = False

                st.session_state.learned_flashcards = set()

                st.session_state.quiz_version = st.session_state.get("quiz_version", 0) + 1

            st.subheader("🧩 Text Chunks")

            st.info(f"Total chunks: {len(chunks)}")

            for index, item in enumerate(chunks_with_pages, start=1):

                with st.expander(f"Chunk {index} — Page {item['page']}"):

                    st.write(item["text"])

            st.divider()

            st.subheader("📝 AI Lecture Summarizer")

            st.write("Generate a concise study summary from your uploaded PDF.")

            st.caption(

                "Summarizes your PDF using a multi-step AI process. "

                "Long documents may take a few minutes."

            )

            if st.button("📝 Generate Summary"):

                with st.spinner("Qwen is summarizing your lecture..."):

                    try:

                        st.session_state.summary = generate_summary(chunks_with_pages)

                    except Exception as error:

                        st.error(f"Could not generate summary: {error}")

            if st.session_state.get("summary") is not None:

                st.success("Summary generated successfully!")

                st.markdown(st.session_state.summary)

                st.download_button(

                    label="📥 Download Summary",

                    data=st.session_state.summary,

                    file_name="StudyMate_Summary.txt",

                    mime="text/plain; charset=utf-8",

                    key="download_summary",

                )

            st.divider()



            st.subheader("🃏 AI Flashcards Generator")

            st.write("Review important concepts from your PDF.")



            num_cards = st.selectbox(

                "Number of flashcards",

                options=[3, 5, 10],

                index=1,

                key="flashcard_count"

            )



            # Previously generated cards can be loaded without running Qwen.
            try:
                saved_cards = get_saved_flashcards(pdf_id)
            except Exception as error:
                saved_cards = []
                st.error(f"Could not check saved flashcards: {error}")

            if saved_cards:
                st.info(f"💾 {len(saved_cards)} saved flashcards found for this PDF.")
                if st.button("📂 Load Saved Flashcards", key="load_saved_flashcards"):
                    try:
                        saved_progress = get_learned_flashcards(pdf_id)
                        st.session_state.flashcards = saved_cards
                        st.session_state.flashcard_index = 0
                        st.session_state.show_flashcard_answer = False
                        st.session_state.learned_flashcards = saved_progress
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not load saved flashcards: {error}")

            if st.button("🃏 Generate Flashcards"):
                with st.spinner("Qwen is generating flashcards..."):
                    try:
                        generated_cards = generate_flashcards(
                            chunks_with_pages, num_cards=num_cards
                        )
                        # Save before replacing the visible deck so errors do not
                        # make an unsaved deck appear to be persisted.
                        if not generated_cards:
                            st.warning("No flashcards were generated.")
                        else:
                            save_flashcards(pdf_id, generated_cards)
                            st.session_state.flashcards = generated_cards
                            st.session_state.flashcard_index = 0
                            st.session_state.show_flashcard_answer = False
                            st.session_state.learned_flashcards = get_learned_flashcards(pdf_id)
                            st.success("💾 Flashcards generated and saved successfully!")
                    except Exception as error:
                        st.error(f"Could not generate or save flashcards: {error}")

            flashcards = st.session_state.get("flashcards")



            if flashcards:

                index = st.session_state.get("flashcard_index", 0)

                index = max(0, min(index, len(flashcards) - 1))

                st.session_state.flashcard_index = index



                card = flashcards[index]



                if "learned_flashcards" not in st.session_state:

                    try:

                        st.session_state.learned_flashcards = get_learned_flashcards(pdf_id)

                    except Exception as error:

                        st.session_state.learned_flashcards = set()

                        st.error(f"Could not load flashcard progress: {error}")



                learned = st.session_state.learned_flashcards

                learned_count = sum(

                    card_item["question"] in learned for card_item in flashcards

                )

                total_cards = len(flashcards)



                st.progress(

                    learned_count / total_cards,

                    text=f"⭐ Learned: {learned_count}/{total_cards}"

                )

                st.caption(f"📚 Remaining: {total_cards - learned_count} cards")



                card_question = card["question"]

                if card_question in learned:

                    st.success("✅ You have learned this card!")

                    if st.button("↩️ Mark as Not Learned"):

                        try:

                            save_flashcard_progress(pdf_id, card_question, False)

                            learned.discard(card_question)

                            st.rerun()

                        except Exception as error:

                            st.error(f"Could not update flashcard progress: {error}")

                else:

                    if st.button("⭐ Mark as Learned"):

                        try:

                            save_flashcard_progress(pdf_id, card_question, True)

                            learned.add(card_question)

                            st.rerun()

                        except Exception as error:

                            st.error(f"Could not save flashcard progress: {error}")



                st.markdown(

                    f"### Card {index + 1} of {len(flashcards)}"

                )

                st.info(card["question"])



                if st.session_state.get("show_flashcard_answer", False):

                    st.success(card["answer"])



                if st.button("👀 Show / Hide Answer"):

                    st.session_state.show_flashcard_answer = not (

                        st.session_state.get(

                            "show_flashcard_answer", False

                        )

                    )

                    st.rerun()



                col_prev, col_next = st.columns(2)



                with col_prev:

                    if st.button(

                        "⬅️ Previous",

                        disabled=index == 0

                    ):

                        st.session_state.flashcard_index -= 1

                        st.session_state.show_flashcard_answer = False

                        st.rerun()



                with col_next:

                    if st.button(

                        "Next ➡️",

                        disabled=index == len(flashcards) - 1

                    ):

                        st.session_state.flashcard_index += 1

                        st.session_state.show_flashcard_answer = False

                        st.rerun()



                if st.button("🔄 Restart Review"):

                    st.session_state.flashcard_index = 0

                    st.session_state.show_flashcard_answer = False

                    st.rerun()



            st.divider()



            st.subheader("🧠 AI Quiz Generator")

            st.write("Generate multiple-choice questions from your uploaded PDF.")

            st.caption(

                "Quiz questions sample different parts of your PDF. "

                "AI-generated answers should be checked against the source."

            )

            num_questions = st.selectbox(

                "Number of questions", options=[3, 5, 10], index=1

            )

            if st.button("🎯 Generate Quiz"):

                st.session_state.quiz = None

                st.session_state.quiz_result = None

                st.session_state.quiz_version += 1

                with st.spinner("Qwen is generating your quiz..."):

                    try:

                        st.session_state.quiz = generate_quiz(

                            chunks_with_pages, num_questions=num_questions

                        )

                    except Exception as error:

                        st.error(f"Could not generate quiz: {error}")

            if st.session_state.get("quiz"):

                quiz = st.session_state.quiz

                version = st.session_state.quiz_version

                st.subheader("📋 Your Quiz")

                with st.form(key=f"quiz_form_{version}"):

                    selected_answers = []

                    for index, item in enumerate(quiz):

                        st.markdown(f"**Question {index + 1}: {item['question']}**")

                        answer = st.radio(

                            "Choose your answer:",

                            options=list(range(4)),

                            format_func=lambda i, opts=item["options"]: opts[i],

                            index=None,

                            key=f"quiz_{version}_question_{index}",

                        )

                        selected_answers.append(answer)

                        st.divider()

                    submitted = st.form_submit_button("✅ Submit Answers")

                if submitted:

                    if any(answer is None for answer in selected_answers):

                        st.warning("Please answer all questions before submitting.")

                    else:

                        st.session_state.quiz_result = list(selected_answers)

                        # Save once per quiz version in the current session.

                        # Re-rendering and downloading do not create extra records.

                        saved_versions = st.session_state.setdefault(

                            "saved_quiz_versions", set()

                        )

                        if version not in saved_versions:

                            attempt_score = sum(

                                answer == item["correct_answer"]

                                for answer, item in zip(selected_answers, quiz)

                            )

                            try:

                                save_quiz_attempt(

                                    uploaded_file.name, attempt_score, len(quiz)

                                )

                                saved_versions.add(version)

                            except Exception as error:

                                st.error(f"Could not save quiz attempt: {error}")

                # Retry the same questions with fresh, unselected radio buttons.

                # A new version changes widget keys without calling Ollama again.

                if st.button("🔄 Retry Quiz", key=f"retry_quiz_{version}"):

                    st.session_state.quiz_result = None

                    st.session_state.quiz_version += 1

                    st.rerun()

                if st.session_state.get("quiz_result") is not None:

                    answers = st.session_state.quiz_result

                    score = sum(

                        answer == item["correct_answer"]

                        for answer, item in zip(answers, quiz)

                    )

                    st.success(f"Your Score: {score}/{len(quiz)} 🎉")

                    # Build a UTF-8 report from the submitted answers.

                    report_lines = [

                        "StudyMate AI - Quiz Results",

                        f"PDF: {uploaded_file.name}",

                        f"Score: {score}/{len(quiz)} ({score / len(quiz) * 100:.1f}%)",

                        "",

                    ]

                    for question_number, (chosen, question_item) in enumerate(

                        zip(answers, quiz), start=1

                    ):

                        correct_index = question_item["correct_answer"]

                        report_lines.extend([

                            f"Question {question_number}: {question_item['question']}",

                            f"Your answer: {question_item['options'][chosen]}",

                            f"Correct answer: {question_item['options'][correct_index]}",

                            "Result: Correct" if chosen == correct_index else "Result: Incorrect",

                            f"Explanation: {question_item['explanation']}",

                            "",

                        ])

                    report_lines.append(

                        "Note: AI-generated questions and answer keys may contain errors."

                    )

                    st.download_button(

                        label="📥 Download Quiz Results",

                        data="\n".join(report_lines).encode("utf-8"),

                        file_name="StudyMate_Quiz_Results.txt",

                        mime="text/plain",

                        key=f"download_quiz_results_{version}",

                    )

                    for index, (answer, item) in enumerate(zip(answers, quiz), start=1):

                        correct = item["correct_answer"]

                        if answer == correct:

                            st.success(f"Question {index}: Correct!")

                        else:

                            st.error(f"Question {index}: Incorrect.")

                        st.write("**Correct answer:** " + item["options"][correct])

                        st.info(item["explanation"])

            st.divider()

            st.subheader("📊 Study Progress Tracker")

            st.caption(

                "Quiz results are saved locally in studymate.db and remain "

                "available after restarting the app. History is grouped by PDF filename."

            )

            try:

                history = get_quiz_attempts(uploaded_file.name)

            except Exception as error:

                history = []

                st.error(f"Could not load saved quiz history: {error}")



            if history:

                best_attempt = max(history, key=lambda entry: entry["percentage"])

                col1, col2, col3 = st.columns(3)

                col1.metric("Total Attempts", len(history))

                col2.metric("Best Score", f"{best_attempt['percentage']:.1f}%")

                col3.metric("Latest Score", f"{history[-1]['percentage']:.1f}%")



                progress_df = pd.DataFrame(history)

                progress_df.insert(0, "attempt", range(1, len(progress_df) + 1))

                st.markdown("**Score Progress**")

                st.line_chart(

                    progress_df.set_index("attempt")[["percentage"]],

                    x_label="Attempt",

                    y_label="Score (%)",

                )

                st.markdown("**Attempt History**")

                st.dataframe(

                    progress_df[["attempt", "score", "total_questions", "percentage", "created_at"]].rename(

                        columns={

                            "attempt": "Attempt",

                            "score": "Correct",

                            "total_questions": "Questions",

                            "percentage": "Score (%)",

                            "created_at": "Date",

                        }

                    ),

                    hide_index=True,

                    width="stretch",

                )

            else:

                st.info("Submit a quiz to start tracking your study progress.")



            st.divider()

            st.subheader("🧠 AI Embeddings")

            if st.button("Generate Embeddings"):

                with st.spinner("Creating embeddings..."):

                    try:
                        model = get_model()
                        st.session_state.embeddings = create_embeddings(chunks, model)
                    except Exception as error:
                        st.error(f"Could not create embeddings: {error}")

            if st.session_state.embeddings is not None:

                embeddings = st.session_state.embeddings

                st.success("Embeddings are ready!")

                st.write(f"Number of chunks: {len(chunks)}")

                st.write(f"Embeddings shape: {embeddings.shape}")

                st.divider()

                st.subheader("🔎 Semantic Search")

                question = st.text_input(

                    "Ask a question about your PDF",

                    placeholder="e.g. What is database normalization?",

                )

                if st.button("Search"):

                    if not question.strip():

                        st.warning("Please enter a question.")

                    else:

                        with st.spinner("Searching..."):

                            model = get_model()

                            results = search_similar_chunks(

                                question=question,

                                chunks=chunks,

                                embeddings=embeddings,

                                model=model,

                                top_k=3,

                            )

                        results_with_pages = [
                            {**result, "page": chunks_with_pages[result["index"]]["page"]}
                            for result in results
                        ]

                        st.subheader("📚 Most Relevant Chunks")

                        for index, result in enumerate(results_with_pages, start=1):

                            page_label = (

                                f" — Page {result['page']}"

                                if result["page"] is not None else ""

                            )

                            st.markdown(f"**Result {index}{page_label}**")

                            st.write(f"Similarity score: {result['score']:.3f}")

                            st.write(result["text"])

                            st.divider()

                        st.subheader("🤖 AI Answer")

                        with st.spinner("Qwen is generating an answer..."):

                            try:

                                answer = generate_answer(

                                    question=question, relevant_chunks=results

                                )

                                st.success("Answer generated successfully!")

                                st.write(answer)

                                st.divider()

                                st.subheader("📚 Sources Used")

                                st.caption(

                                    "These are the retrieved PDF chunks provided "

                                    "to the AI, not verified citations. "

                                    "Page numbers refer to actual PDF pages."

                                )

                                for index, result in enumerate(results_with_pages, start=1):

                                    page_label = (

                                        f"Page {result['page']}"

                                        if result["page"] is not None else "Page unknown"

                                    )

                                    with st.expander(f"Source {index} — {page_label}"):

                                        st.caption(

                                            f"Similarity score: {result['score']:.3f}"

                                        )

                                        st.write(result["text"])

                            except Exception as error:

                                st.error(f"Could not generate an AI answer: {error}")

        elif has_text:

            st.warning("No text chunks could be created from this PDF.")

    except Exception as error:

        st.error(f"Could not read the PDF: {error}")
