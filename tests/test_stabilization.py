from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pymupdf
from src import database, flashcards, quiz_generator
from src.semantic_search import search_similar_chunks
from src.text_chunker import split_pdf_pages, split_text


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.patch = patch.object(database, 'DB_PATH', Path(self.temp.name) / 'test.db')
        self.patch.start()
        database.init_database()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_existing_schema_and_progress_survive_initialization(self):
        database.save_quiz_attempt('lecture.pdf', 2, 3)
        database.save_flashcard_progress('pdf', 'Question?', True)
        with closing(sqlite3.connect(database.DB_PATH)) as connection, connection:
            connection.execute('DROP TABLE flashcard_decks')
        database.init_database()
        self.assertEqual(database.get_saved_flashcards('pdf'), [])
        self.assertEqual(database.get_quiz_attempts('lecture.pdf')[0]['percentage'], 66.67)
        self.assertEqual(database.get_learned_flashcards('pdf'), {'Question?'})
        self.assertEqual(database.get_quiz_attempts('other.pdf'), [])

    def test_deck_round_trip_replacement_and_isolation(self):
        cards = [{'question': 'מה?', 'answer': 'Unicode answer'}]
        database.save_flashcards('pdf', cards)
        self.assertEqual(database.get_saved_flashcards('pdf'), cards)
        self.assertEqual(database.get_saved_flashcards('other'), [])
        database.save_flashcard_progress('pdf', 'מה?', True)
        database.save_flashcards('pdf', [{'question': 'New?', 'answer': 'New answer'}])
        self.assertEqual(len(database.get_saved_flashcards('pdf')), 1)
        self.assertEqual(database.get_learned_flashcards('pdf'), {'מה?'})
        database.save_flashcard_progress('pdf', 'מה?', False)
        self.assertEqual(database.get_learned_flashcards('pdf'), set())

    def test_invalid_deck_preserves_saved_data(self):
        cards = [{'question': 'Q', 'answer': 'A'}]
        database.save_flashcards('pdf', cards)
        for bad in ([], [{}], cards * 2):
            with self.assertRaises(ValueError):
                database.save_flashcards('pdf', bad)
        self.assertEqual(database.get_saved_flashcards('pdf'), cards)

    def test_invalid_score(self):
        for score, total in ((1, 0), (-1, 3), (4, 3)):
            with self.assertRaises(ValueError):
                database.save_quiz_attempt('pdf', score, total)


class ContentTests(unittest.TestCase):
    def test_actual_pdf_pages_include_blank_page(self):
        with pymupdf.open() as pdf:
            pdf.new_page().insert_text((72, 72), 'First page')
            pdf.new_page()
            pdf.new_page().insert_text((72, 72), 'Third page')
            chunks = split_pdf_pages(pdf)
        self.assertEqual([c['page'] for c in chunks], [1, 3])
        with self.assertRaises(ValueError):
            split_text('abc', chunk_size=2, overlap=2)

    def test_duplicate_text_retains_retrieved_index(self):
        model = Mock()
        model.encode.return_value = np.array([1., 0.])
        results = search_similar_chunks('q', ['same', 'same'], np.array([[0., 1.], [1., 0.]]), model)
        self.assertEqual(results[0]['index'], 1)

    def test_flashcards_mocked_ollama(self):
        response = Mock()
        response.json.return_value = {'response': '{"flashcards":[{"question":"Q","answer":"A"}]}'}
        with patch.object(flashcards.requests, 'post', return_value=response):
            self.assertEqual(flashcards.generate_flashcards([{'page': 1, 'text': 'notes'}], 1)[0]['answer'], 'A')
        self.assertEqual(flashcards.select_chunks([1, 2], 1), [1])

    def test_quiz_rejects_boolean_answer(self):
        response = Mock()
        response.json.return_value = {'response': '{"questions":[{"question":"Q","options":["a","b","c","d"],"correct_answer":true,"explanation":"E"}]}'}
        with patch.object(quiz_generator.requests, 'post', return_value=response):
            with self.assertRaises(ValueError):
                quiz_generator.generate_quiz([{'page': 1, 'text': 'notes'}], 1)

    def test_app_starts_with_temporary_storage(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(database, 'DB_PATH', Path(folder) / 'app.db'):
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=60)
                self.assertEqual(len(app.exception), 0)
                self.assertEqual(app.title[0].value, '🎓 StudyMate AI')

    def test_uploaded_pdf_saved_deck_and_quiz_retry(self):
        import hashlib
        import streamlit as st
        from streamlit.testing.v1 import AppTest
        from types import SimpleNamespace
        with pymupdf.open() as pdf:
            pdf.new_page().insert_text((72, 72), "Study notes for testing")
            content = pdf.tobytes()
        upload = SimpleNamespace(name="test.pdf", size=len(content), getvalue=lambda: content)
        pdf_id = hashlib.sha256(content).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(database, 'DB_PATH', Path(folder) / 'app.db'), patch.object(st, 'file_uploader', return_value=upload):
                database.init_database()
                database.save_flashcards(pdf_id, [{"question": "Q", "answer": "A"}])
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=60)
                self.assertEqual(len(app.exception), 0)
                app.button(key="load_saved_flashcards").click().run()
                self.assertEqual(app.session_state['flashcards'][0]['answer'], 'A')
                next(b for b in app.button if 'Mark as Learned' in b.label).click().run()
                self.assertEqual(database.get_learned_flashcards(pdf_id), {'Q'})
                app.session_state['quiz'] = [{"question": "Quiz Q", "options": ["a", "b", "c", "d"], "correct_answer": 0, "explanation": "Explanation"}]
                app.run()
                app.radio[0].set_value(0)
                next(b for b in app.button if 'Submit Answers' in b.label).click().run()
                self.assertEqual(database.get_quiz_attempts('test.pdf')[0]['score'], 1)
                app.run()
                self.assertEqual(len(database.get_quiz_attempts('test.pdf')), 1)
                next(b for b in app.button if 'Retry Quiz' in b.label).click().run()
                self.assertIsNone(app.radio[0].value)
                self.assertIsNone(app.session_state['quiz_result'])
                self.assertEqual(len(app.exception), 0)


if __name__ == '__main__':
    unittest.main()
