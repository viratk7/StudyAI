import re
from typing import List, Tuple, TypedDict

import fitz  # PyMuPDF

CHAPTER_REGEX = re.compile(
    r"""
    ^(
        # Chapter keyword formats
        (chapter|chap|ch)\.?\s*(\d+|[ivxlcdm]+) |

        # Numbered titles like "1." or "1:"
        (\d+)\s*[\.\:\-]\s* |

        # Roman numeral headings like "IV."
        ([ivxlcdm]+)\s*[\.\:\-]\s* |

        # Number with title (no dot)
        (\d+)\s+[A-Z]
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def is_chapter(title: str) -> bool:
    return bool(CHAPTER_REGEX.match(title.strip()))


def get_chapters(doc) -> List[Tuple[str, int]]:
    toc = doc.get_toc()
    chapters = []

    for _, title, page in toc:
        if is_chapter(title):
            chapters.append((title, page))

    return chapters


def get_chapter_ranges(
    chapters: List[Tuple[str, int]], doc
) -> List[Tuple[str, int, int]]:
    chapter_ranges = []

    for i in range(len(chapters)):
        title, start = chapters[i]

        if i + 1 < len(chapters):
            end = chapters[i + 1][1] - 1
        else:
            end = doc.page_count

        chapter_ranges.append((title, start, end))

    return chapter_ranges


def extract_text(doc, start: int, end: int) -> str:
    text = ""

    for i in range(start - 1, end):  # fix indexing
        page = doc[i]
        text += page.get_text()

    text = text.replace("\n", " ")
    return text


def split_pdf(input_path, output_path, start_page, end_page):
    doc = fitz.open(input_path)
    new_doc = fitz.open()

    # PyMuPDF is 0-indexed
    for i in range(start_page - 1, end_page):
        new_doc.insert_pdf(doc, from_page=i, to_page=i)

    new_doc.save(output_path)
    new_doc.close()
    doc.close()


class Chapter(TypedDict):
    title: str
    start_page: int
    end_page: int
    content: str
    file_path: str


def final_doc_to_split(book_pdf_path: str, book_dir: str,book_id:int) -> List[Chapter]:
    # takes pdf and splits pdf into chapters
    doc = fitz.open(book_pdf_path)
    chapters = get_chapters(doc)
    ranges = get_chapter_ranges(chapters, doc)

    chapter_data = []
    for title, start, end in ranges:
        content = extract_text(doc, start, end)
        chapter_data.append(
            {
                "title": title,
                "start_page": int(start),
                "end_page": int(end),
                "content": content,
            }
        )

    temp = 0
    for chapter in chapter_data:
        temp += 1
        file_path = f"{book_dir}/{temp}.pdf"
        split_pdf(book_pdf_path, file_path, chapter["start_page"], chapter["end_page"])
        chapter["file_path"] = f"uploads/{book_id}/{temp}.pdf"

    return chapter_data
