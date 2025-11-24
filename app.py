from flask import Flask, render_template, request, redirect
import sqlite3
import random
import datetime

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('private_library.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,  
            name TEXT ,
            credit_score INTEGER DEFAULT 500
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE, 
            title TEXT , 
            author TEXT ,
            tag TEXT  ,
            copies INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS issued_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            book_id INTEGER UNIQUE,
            issue_date TEXT,
            return_date TEXT,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()
    
# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Add book
@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    tag = request.form['tag']
    copies = int(request.form['copies'])

    conn = sqlite3.connect('private_library.db')
    c = conn.cursor()
    c.execute("INSERT INTO books (title, author, tag, copies) VALUES (?, ?, ?, ?)",
              (title, author, tag, copies))
    conn.commit()
    conn.close()
    return redirect('/books')

# View books
@app.route('/books')
def books():
    conn = sqlite3.connect('private_library.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    conn.close()
    return render_template('books.html', books=books)

# Add user
@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    conn = sqlite3.connect('private_library.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    return redirect('/users')

# View users and issue books
@app.route('/users')
def users():
    conn = sqlite3.connect('private_library.db')
    # conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM books")
    books = c.fetchall()
    c.execute("SELECT * FROM issued_books")
    issued_books = c.fetchall()
    conn.close()
    return render_template('users.html', users=users, books=books, issued_books=issued_books)

# Issue book
@app.route('/issue_book', methods=['POST'])
def issue_book():
    user_id = int(request.form['user_id'])
    book_id = int(request.form['book_id'])
    issue_date = datetime.date.today().isoformat()

    conn = sqlite3.connect('private_library.db')
    c = conn.cursor()

    c.execute("SELECT credit_score FROM users WHERE id=?", (user_id,))
    score = c.fetchone()[0]

    c.execute("SELECT tag, copies FROM books WHERE id=?", (book_id,))
    tag, copies = c.fetchone()

    if copies <= 0:
        conn.close()
        return "No copies available."

    if tag == "premium" and score < 300:
        conn.close()
        return "User not eligible for premium books."

    c.execute("INSERT INTO issued_books (user_id, book_id, issue_date, status) VALUES (?, ?, ?, ?)",
              (user_id, book_id, issue_date, "issued"))
    c.execute("UPDATE books SET copies = copies - 1 WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return redirect('/users')

# Return book
@app.route('/return_book/<int:issue_id>')
def return_book(issue_id):
    today = datetime.date.today()

    conn = sqlite3.connect('private_library.db')
    c = conn.cursor()

    c.execute("SELECT user_id, book_id, issue_date FROM issued_books WHERE id=?", (issue_id,))
    user_id, book_id, issue_date = c.fetchone()
    issue_date = datetime.date.fromisoformat(issue_date)

    c.execute("UPDATE issued_books SET return_date=?, status=? WHERE id=?",
              (today.isoformat(), "returned", issue_id))

    days = (today - issue_date).days
    if days > 7:
        c.execute("UPDATE users SET credit_score = credit_score - 50 WHERE id=?", (user_id,))
    else:
        c.execute("UPDATE users SET credit_score = credit_score + 20 WHERE id=?", (user_id,))

    c.execute("UPDATE books SET copies = copies + 1 WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return redirect('/users')

print("Connected to:", "")

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0",port=10000, debug=True)