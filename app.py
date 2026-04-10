from flask import Flask,render_template,request,redirect
from flask import session
import sqlite3
import os
from datetime import date
streak=0
last_completed_date=None

app=Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER='static/uploads'

app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
import os

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
tasks=[]

#----------DATABASE SETUP---------
def get_db_connection():
    conn=sqlite3.connect('tasks.db')
    conn.row_factory=sqlite3.Row
    return conn


#----create table---------
# Create tasks table
conn = get_db_connection()
conn.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT,
    done INTEGER,
    day TEXT,
    user_id TEXT
)
''')
conn.close()

# Create users table
conn = get_db_connection()
conn.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')
conn.close()


#------ROUTES--------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, password)
            )
            conn.commit()
        except:
            return "User already exists"

        conn.close()
        return redirect('/login')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect('/')
        else:
            return "Invalid credentials"

    return render_template('login.html')


@app.route('/')
@app.route('/')
def index():

    # 🔒 Protect route
    if 'user' not in session:
        return redirect('/login')

    user = session['user']   # ✅ safe now

    upload_folder = app.config['UPLOAD_FOLDER']

    import os
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    files = os.listdir(upload_folder)

    conn = get_db_connection()
    tasks = conn.execute(
        'SELECT * FROM tasks WHERE user_id = ? ORDER BY day',
        (user,)
    ).fetchall()
    conn.close()

    streak = sum(1 for task in tasks if task['done'] == 1)

    return render_template('index.html', tasks=tasks, files=files, streak=streak)

upload_folder = app.config['UPLOAD_FOLDER']

import os
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

files = os.listdir(upload_folder)

@app.route('/add',methods=['POST'])
def add():
    task=request.form.get('task')
    day=request.form.get('day')
    conn=get_db_connection()
    conn.execute(
    'INSERT INTO tasks (task, done, day, user_id) VALUES (?, ?, ?, ?)',
    (task, 0, day, session['user'])
)
    conn.commit()
    conn.close()
    #tasks.append({'task':task,'done':False})
    return redirect('/')


@app.route('/toggle/<int:id>', methods=['POST'])
def toggle(id):
    global streak, last_completed_date

    conn = get_db_connection()
    task = conn.execute('SELECT done FROM tasks WHERE id = ?', (id,)).fetchone()
    new_status = 0 if task['done'] else 1

    conn.execute('UPDATE tasks SET done = 1 WHERE id = ? AND user_id = ?',(id, session['user']))
    conn.commit()
    conn.close()

    today = date.today()

    if new_status == 1:
        if last_completed_date == today:
            pass
        elif last_completed_date is None or (today - last_completed_date).days == 1:
            streak += 1
        else:
            streak = 1

        last_completed_date = today

    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    conn=get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?',(id, session['user']))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

@app.route('/upload',methods=['POST'])
def upload():
    file=request.files['file']
    if file:
        filepath=os.path.join(app.config['UPLOAD_FOLDER'],file.filename)
        file.save(filepath)
    return redirect('/')
    
if __name__ =='__main__':
    app.run(debug=True)

