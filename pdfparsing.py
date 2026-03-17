import re
import fitz  # PyMuPDF
import time
from typing import List,Tuple

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


def is_chapter(title:str)->bool:
    return bool(CHAPTER_REGEX.match(title.strip()))


def get_chapters(doc)->List[Tuple[str,int]]:
    toc = doc.get_toc()
    chapters = []
    
    for _,title, page in toc:
        if is_chapter(title):
            chapters.append((title, page))
            
    return chapters


def get_chapter_ranges(chapters:List[Tuple[str,int]], doc)->List[Tuple[str,int,int]]:
    chapter_ranges = []

    for i in range(len(chapters)):
        title, start = chapters[i]

        if i + 1 < len(chapters):
            end = chapters[i + 1][1] - 1
        else:
            end = doc.page_count

        chapter_ranges.append((title, start, end))

    return chapter_ranges

def extract_text(doc, start:int, end:int)->str:
    text = ""
    
    for i in range(start - 1, end):  # fix indexing
        page = doc[i]
        text += page.get_text()
        
    text = text.replace("\n", " ")
    return text

doc = fitz.open("book.pdf")
chapters=get_chapters(doc)
ranges = get_chapter_ranges(chapters, doc)

chapter_data=[]
for title, start, end in ranges:
    content = extract_text(doc, start, end)
    
    chapter_data.append({
        "title": title,
        "start_page": int(start),
        "end_page": int(end),
        "content": content
    })
    

def split_pdf(input_path, output_path, start_page, end_page):
    doc = fitz.open(input_path)
    new_doc = fitz.open()

    # PyMuPDF is 0-indexed
    for i in range(start_page - 1, end_page):
        new_doc.insert_pdf(doc, from_page=i, to_page=i)

    new_doc.save(output_path)
    new_doc.close()
    doc.close()

temp=0
s1=time.time()
for chapter in chapter_data:
    temp+=1
    split_pdf("book.pdf", f"chapters/{temp}.pdf", chapter["start_page"],chapter["end_page"])
e1=time.time()
print("Time Taken: ",e1-s1)