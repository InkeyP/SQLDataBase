from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)


@app.route('/init')
def init_db():
    print("Initializing database...")

    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()

    # 创建表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stu_id INTEGER NOT NULL,
        course_name TEXT NOT NULL,
        course_score INTEGER NOT NULL,
        FOREIGN KEY (stu_id) REFERENCES students(id)
    )''')

    # 插入示例数据
    cursor.execute("INSERT OR IGNORE INTO students (id, student_name) VALUES (1, 'Alice')")
    cursor.execute("INSERT OR IGNORE INTO students (id, student_name) VALUES (2, 'Bob')")

    cursor.execute("INSERT OR IGNORE INTO courses (id, stu_id, course_name, course_score) VALUES (1, 1, 'Math', 85)")
    cursor.execute("INSERT OR IGNORE INTO courses (id, stu_id, course_name, course_score) VALUES (2, 1, 'English', 92)")
    cursor.execute("INSERT OR IGNORE INTO courses (id, stu_id, course_name, course_score) VALUES (3, 2, 'Math', 78)")
    cursor.execute("INSERT OR IGNORE INTO courses (id, stu_id, course_name, course_score) VALUES (4, 2, 'English', 88)")

    conn.commit()
    conn.close()

    return "Database initialized."


@app.route('/', methods=['GET', 'POST'])
def student():
    student_name = request.args.get('student_name', '')
    query = '''
        SELECT students.student_name, courses.course_name, courses.course_score
        FROM courses
        JOIN students ON courses.stu_id = students.id
    '''
    params = ()

    # 如果用户提供了学生姓名，附加过滤条件
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
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()

    # 处理增删改查请求
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_student':
            student_name = request.form.get('student_name')
            cursor.execute("INSERT INTO students (student_name) VALUES (?)", (student_name,))

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

    # 查询现有数据以展示
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    conn.close()

    return render_template('admin.html', students=students, courses=courses)


if __name__ == '__main__':
    app.run(debug=True)
