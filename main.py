import uvicorn
from fastapi import FastAPI,UploadFile
from fastapi.staticfiles import StaticFiles
from db import init_db
from fastapi.middleware.cors import CORSMiddleware
from services import get_books, delete_from_db, create_to_db, get_chapter

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()

@app.get("/books")
def get_all_books():
    return get_books()

@app.post("/upload")
async def upload(file: UploadFile):
    return create_to_db(file=file)
    
@app.get("/book_chapters")
def get_book_chapters(book_id:int):
    return get_chapter(book_id)


@app.delete("/delete_book")
def delete_post(book_id:int):
    return delete_from_db(book_id)


if __name__=="__main__":
    uvicorn.run("main:app", host="0.0.0.0",port=8000, reload=True)