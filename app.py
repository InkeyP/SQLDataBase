from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'inkey'


@app.route('/init')
def init_db():
    print("Initializing database...")

    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL UNIQUE,
        student_password TEXT NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stu_id INTEGER NOT NULL,
        course_name TEXT NOT NULL,
        course_score INTEGER NOT NULL,
        FOREIGN KEY (stu_id) REFERENCES students(id)
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )''')

    cursor.execute("INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)", ('admin', 'admin123'))

    students = [
        ('Inkey', 'inkey233'),
        ('W36', 'ww3636'),
        ('Showmaker', 'twogoat')
    ]
    cursor.executemany("INSERT OR IGNORE INTO students (student_name, student_password) VALUES (?, ?)", students)

    courses = [
        (1, 1, 'Math', 85),
        (2, 1, 'English', 92),
        (3, 2, 'Math', 98),
        (4, 2, 'English', 96),
        (5, 3, 'Math', 78),
        (6, 3, 'English', 88)
    ]
    cursor.executemany("INSERT OR IGNORE INTO courses (id, stu_id, course_name, course_score) VALUES (?, ?, ?, ?)",
                       courses)

    conn.commit()
    conn.close()

    return "数据库初始完成"


@app.route('/', methods=['GET'])
def index():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        return redirect('/admin')
    elif 'student_logged_in' in session and session['student_logged_in']:
        return redirect('/student')
    else:
        return redirect('/login')
@app.route('/student', methods=['GET', 'POST'])
def student():
    student_name = request.args.get('student_name', '')
    query = '''
        SELECT students.student_name, courses.course_name, courses.course_score
        FROM courses
        JOIN students ON courses.stu_id = students.id
    '''
    params = ()

    if student_name:
        query += ' WHERE students.student_name = ?'
        params = (student_name,)

    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
    except Exception as e:
        results = []
        print(f"SQL Error: {e}")
    conn.close()

    return render_template('student.html', results=results, student_name=student_name)


@app.route('/admin', methods=['GET', 'POST'])
def teacher():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return redirect('/login')

    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_student':
            student_name = request.form.get('student_name')
            cursor.execute("INSERT INTO students (student_name, student_password) VALUES (?, ?)", (student_name, '12345678',))

        elif action == 'delete_student':
            student_id = request.form.get('student_id')
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))

        elif action == 'update_student':
            student_id = request.form.get('student_id')
            new_name = request.form.get('new_name')
            cursor.execute("UPDATE students SET student_name = ? WHERE id = ?", (new_name, student_id))

        elif action == 'add_course':
            stu_id = request.form.get('stu_id')
            course_name = request.form.get('course_name')
            course_score = request.form.get('course_score')
            cursor.execute("INSERT INTO courses (stu_id, course_name, course_score) VALUES (?, ?, ?)",
                           (stu_id, course_name, course_score))

        elif action == 'delete_course':
            course_id = request.form.get('course_id')
            cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))

        elif action == 'update_course':
            course_id = request.form.get('course_id')
            new_name = request.form.get('new_name')
            new_score = request.form.get('new_score')
            cursor.execute("UPDATE courses SET course_name = ?, course_score = ? WHERE id = ?",
                           (new_name, new_score, course_id))

        conn.commit()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    conn.close()

    return render_template('admin.html', students=students, courses=courses)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        if user_type == 'student':
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            query = f"SELECT * FROM students WHERE student_name = '{username}' AND student_password = '{password}'"
            cursor.execute(query)
            stu = cursor.fetchone()
            conn.close()

            if stu:
                session['student_logged_in'] = True
                return redirect('/student')
            else:
                error = "错误的账号或密码"

        if user_type == 'teacher':
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            query = f"SELECT * FROM admin WHERE username = '{username}' AND password = '{password}'"
            cursor.execute(query)
            admin = cursor.fetchone()
            conn.close()

            if admin:
                session['admin_logged_in'] = True
                session['admin_username'] = username
                return redirect('/admin')
            else:
                error = "错误的账号或密码"

    return render_template('index.html', error=error)


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('student_logged_in', None)
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
