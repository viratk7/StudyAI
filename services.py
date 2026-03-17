from pathlib import Path
from fastapi import HTTPException, UploadFile
from db import get_connection
import shutil
from pdfparsing import final_doc_to_split

PROJECT_ROOT = Path(__file__).resolve().parent
UPLOADS_DIR = PROJECT_ROOT / "uploads"

def create_to_db(file: UploadFile):
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF allowed")
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(book_id) from books")
    result = cursor.fetchone()
    max_id = result[0] if result[0] else 0

    book_id = max_id + 1
    
    book_dir = UPLOADS_DIR / str(book_id)
    book_dir.mkdir(parents=True, exist_ok=True)
    
    original_path = book_dir / "original.pdf"
    with open(original_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    chapter_data = final_doc_to_split(str(original_path), str(book_dir),book_id)

    cursor.execute(
        "INSERT INTO books (book_id,title,file_path) VALUES (?, ?, ?)",
        (book_id, file.filename, str(book_dir)),
    )
    chapter_pdf_paths=[]
    for chapter in chapter_data:
        chapter_pdf_paths.append(chapter["file_path"])
        cursor.execute(
            "INSERT INTO chapters (book_id, chapter_name, file_path, content) VALUES (?, ?, ?, ?)",
            (book_id, chapter["title"], chapter["file_path"], chapter["content"]),
        )
        
    conn.commit()
    conn.close()

    return {
        "id": book_id,
        "title": file.filename,
        "pdf_url": [
            f"http://localhost:8000/{path}"
            for path in chapter_pdf_paths
        ]
    }

def get_chapter(book_id:int):
    conn=get_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT id,chapter_name,file_path FROM chapters WHERE book_id=?",(book_id,))
    data = cursor.fetchall()
    conn.close()
    return [dict(row) for row in data]

def delete_from_db(book_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM books WHERE book_id = ?", (book_id,))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Book not found")

    cursor.execute("DELETE FROM chapters WHERE book_id = ?", (book_id,))

    conn.commit()
    conn.close()
    
def get_books():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY book_id DESC")
    data = cursor.fetchall()
    conn.close()
    return [dict(row) for row in data]



