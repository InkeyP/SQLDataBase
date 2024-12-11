from flask import Flask, render_template, request, redirect, session, jsonify
import psycopg2

app = Flask(__name__)
app.secret_key = 'inkey'

# Database configuration
DATABASE_CONFIG = {
    "database": "data",
    "user": "admin",
    "password": "123456",
    "host": "127.0.0.1",
    "port": "54321"
}

# Utility function to connect to the database
def get_db_connection():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"数据库连接失败: {e}")
        return None


@app.route('/', methods=['GET'])
def index():
    if 'admin_logged_in' in session and session['admin_logged_in']:
        return redirect('/admin')
    elif 'student_logged_in' in session and session['student_logged_in']:
        return redirect('/student')
    else:
        return redirect('/login')


@app.route('/admin', methods=['GET'])
def admin():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return redirect('/login')

    conn = get_db_connection()
    if not conn:
        return "无法连接到数据库，请稍后重试。"

    try:
        cursor = conn.cursor()

        # 获取学生数据
        cursor.execute("SELECT id, student_name, gender, profession, student_password FROM students")
        students = cursor.fetchall()

        # 获取课程数据
        cursor.execute("SELECT * FROM courses")
        courses = cursor.fetchall()

        # 获取统计数据
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM courses")
        course_count = cursor.fetchone()[0] or 0

        # 获取性别分布数据
        cursor.execute("SELECT COALESCE(gender, '未知') AS gender, COUNT(*) FROM students GROUP BY gender")
        gender_data = cursor.fetchall()
        gender_chart_data = {
            "labels": [row[0] for row in gender_data],
            "values": [row[1] for row in gender_data],
        }

        # 获取专业分布数据
        cursor.execute("SELECT COALESCE(profession, '未知') AS profession, COUNT(*) FROM students GROUP BY profession")
        profession_data = cursor.fetchall()
        profession_chart_data = {
            "labels": [row[0] for row in profession_data],
            "values": [row[1] for row in profession_data],
        }

    except Exception as e:
        print(f"数据库查询失败: {e}")
        return "系统内部错误，请稍后重试。", 500
    finally:
        conn.close()

    return render_template(
        'admin.html',
        students=students,
        courses=courses,
        student_count=student_count,
        course_count=course_count,
        gender_data=gender_chart_data,
        profession_data=profession_chart_data
    )





@app.route('/update_student', methods=['POST'])
def update_student():
    student_id = request.form.get('id')
    name = request.form.get('name')
    gender = request.form.get('gender')
    profession = request.form.get('profession')
    password = request.form.get('password')

    conn = get_db_connection()
    if not conn:
        return "无法连接到数据库，请稍后重试。"

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE students
            SET student_name = %s, gender = %s, profession = %s, student_password = %s
            WHERE id = %s
        ''', (name, gender, profession, password, student_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"更新学生信息失败: {e}")
        return "更新失败"
    finally:
        conn.close()

    return redirect('/admin')

@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form.get('name')
    gender = request.form.get('gender')
    profession = request.form.get('profession')
    password = request.form.get('password')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (student_name, gender, profession, student_password) VALUES (%s, %s, %s, %s)", (name, gender, profession, password))
    conn.commit()
    conn.close()
    return redirect('/admin')

@app.route('/add_course', methods=['POST'])
def add_course():
    student_id = request.form.get('student_id')
    course_name = request.form.get('course_name')
    score = request.form.get('score')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (stu_id, course_name, course_score) VALUES (%s, %s, %s)", (student_id, course_name, score))
    conn.commit()
    conn.close()
    return redirect('/admin')


@app.route('/update_course', methods=['POST'])
def update_course():
    course_id = request.form.get('id')
    student_id = request.form.get('student_id')
    course_name = request.form.get('course_name')
    score = request.form.get('score')

    conn = get_db_connection()
    if not conn:
        return "无法连接到数据库，请稍后重试。"

    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE courses
            SET stu_id = %s, course_name = %s, course_score = %s
            WHERE id = %s
        ''', (student_id, course_name, score, course_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"更新课程信息失败: {e}")
        return "更新失败"
    finally:
        conn.close()

    return redirect('/admin')


@app.route('/delete', methods=['POST'])
def delete_record():
    record_type = request.form.get('type')  # 获取记录类型
    record_id = request.form.get('id')     # 获取记录 ID

    if not record_type or not record_id:
        return "参数错误，请重试。", 400

    conn = get_db_connection()
    if not conn:
        return "无法连接到数据库，请稍后重试。", 500

    cursor = conn.cursor()
    try:
        if record_type == 'student':
            cursor.execute("DELETE FROM students WHERE id = %s", (record_id,))
        elif record_type == 'course':
            cursor.execute("DELETE FROM courses WHERE id = %s", (record_id,))
        else:
            return "无效的记录类型。", 400

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"删除失败: {e}")
        return "删除失败，请检查记录是否存在或联系管理员。", 500
    finally:
        conn.close()

    return redirect('/admin')

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

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
    except Exception as e:
        results = []
        print(f"SQL Error: {e}")
    conn.close()

    return render_template('student.html', results=results, student_name=student_name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']

        conn = get_db_connection()
        if not conn:
            return "无法连接到数据库，请稍后重试。"

        cursor = conn.cursor()
        try:
            if user_type == 'student':
                query = "SELECT * FROM students WHERE student_name = %s AND student_password = %s"
                cursor.execute(query, (username, password))
                stu = cursor.fetchone()
                if stu:
                    session['student_logged_in'] = True
                    return redirect('/student')
                else:
                    error = "错误的账号或密码"

            elif user_type == 'teacher':
                query = "SELECT * FROM admin WHERE username = %s AND password = %s"
                cursor.execute(query, (username, password))
                admin = cursor.fetchone()
                if admin:
                    session['admin_logged_in'] = True
                    session['admin_username'] = username
                    return redirect('/admin')
                else:
                    error = "错误的账号或密码"
        except Exception as e:
            print(f"查询失败: {e}")
        finally:
            conn.close()

    return render_template('index.html', error=error)


@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('student_logged_in', None)
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
