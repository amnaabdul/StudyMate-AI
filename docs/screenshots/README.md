# Application screenshot checklist and review

Nine real application captures are included in the main README gallery. The project owner approved publication of the current screenshot documentation and images.

## Current captures

| File | Gallery section | Review |
| --- | --- | --- |
| `Main Interface.png` | Main interface and PDF upload | Title and uploaded synthetic filename are readable; the page-count panel is partly clipped at the bottom. |
| `AI Summarizer.png` | AI lecture summarizer | Generated summary is readable; the section heading, end of the summary, and download button are outside the crop. |
| `Flashcards.png` | Flashcard generation and review | Five-card deck, question, and navigation are visible; answer is hidden and a lower control is partly clipped. |
| `MarkedFlashcards.png` | Saved flashcards and learned progress | Saved-deck controls and learned progress of 2/5 are clear; answer is hidden. |
| `Quiz Generator.png` | Multiple-choice quiz generation | Generated questions are readable; submitted answers, score, and explanations are not shown. |
| `Semantic Search.png` | Semantic search and PDF sources | Query, scores, passages, and page references are visible; lower passage text is clipped and no AI answer is shown. |

All nine images preserve the real purple interface. They are about 2700 pixels wide and each is below 400 KB, so the originals are retained without resizing or altering UI content. Open images at full size if text is small in GitHub's README column.

No visible personal names, emails, private filesystem paths, credentials, browser tabs, or notifications were found. PNG metadata contains only standard color, gamma, and resolution information. The visible SQL example uses generic column names rather than real student records.

The captures show **StudyMate_AI_Test_Lecture.pdf**, a two-page synthetic database/SQL lecture. The retrieved text explicitly identifies it as synthetic test material. This is a different document from the earlier three-page demo; [SAMPLE_NOTES.md](SAMPLE_NOTES.md) remains an optional synthetic sample, not the exact source of these screenshots.

## Completed additional captures

| File | Gallery section | Review |
| --- | --- | --- |
| `Quiz Results.png` | Quiz results and explanations | Shows 4/5, retry/download controls, and explanations. A narrow strip at the bottom lies outside app content but exposes no personal information. |
| `Study Progress.png` | Study progress dashboard | Shows one synthetic attempt at 80% and its history. Metric text has low contrast; the chart has no visible trend with a single attempt. The gallery caption reflects this limitation. |
| `AI Answers.png` | AI question answering | Answer is readable and three source references identify page 1. Source panels are collapsed; the gallery does not claim to show expanded passages. |

The new images were reviewed for visible private information and standard PNG metadata. No credentials, personal names, private paths, or private document content were found. All originals are preserved.

## Capture and review procedure

1. Launch local Ollama and the real app using the commands in the main README. Upload only synthetic material.
2. Use **Win+Shift+S** to crop application content. Exclude file pickers, terminals, private paths, browser tabs, bookmarks, taskbar, and unrelated notifications.
3. Keep headings and the complete relevant controls/results within the crop. Avoid cutting off the first or last line of text. Do not fabricate outputs or edit scores.
4. Save readable PNGs, preferably below 1 MB. Lossless compression is optional; do not upscale or repaint the interface.
5. Review visible content and metadata for personal information. Do not delete or replace the local database to prepare screenshots.
6. Add only existing, reviewed images to README using relative Markdown paths and descriptive alt text. For filenames containing spaces, wrap the relative path in angle brackets.
7. Run tests and `git diff --check`, then request explicit approval before committing or pushing screenshots and documentation.

The demo PDFs and SQLite data stay ignored by Git. Only the reviewed screenshot PNGs, this documentation, the synthetic sample notes, and the main README belong in the screenshot documentation commit.
