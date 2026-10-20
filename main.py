import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow frontend requests (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "grading_system.db"

# Helper function to establish connection to the SQLite file
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Enables accessing columns by header name
    return conn

# Create the SQLite table automatically if it doesn't exist yet
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            math_score REAL NOT NULL,
            science_score REAL NOT NULL,
            english_score REAL NOT NULL,
            history_score REAL NOT NULL,
            total_grade REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Run database setup on startup
init_db()

class GradeSchema(BaseModel):
    student_name: str
    math_score: float
    science_score: float
    english_score: float
    history_score: float

def compute_total_grade(math_score: float, science_score: float, english_score: float, history_score: float) -> float:
    return (math_score + science_score + english_score + history_score) / 4

@app.get("/api/grades")
def get_all_grades():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM grades")
    rows = cursor.fetchall()
    conn.close()
    
    # Convert database rows into a list of dictionaries
    return [dict(row) for row in rows]

@app.post("/api/grades")
def add_grade(data: GradeSchema):
    total = compute_total_grade(data.math_score, data.science_score, data.english_score, data.history_score)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert new record into the database table
    cursor.execute("""
        INSERT INTO grades (student_name, math_score, science_score, english_score, history_score, total_grade)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data.student_name, data.math_score, data.science_score, data.english_score, data.history_score, total))
    
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    new_entry = {
        "id": new_id,
        "student_name": data.student_name,
        "math_score": data.math_score,
        "science_score": data.science_score,
        "english_score": data.english_score,
        "history_score": data.history_score,
        "total_grade": total
    }
    return {"status": "success", "data": new_entry}

@app.delete("/api/grades/{grade_id}")
def delete_grade(grade_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grades WHERE id = ?", (grade_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Grade record {grade_id} deleted"}
