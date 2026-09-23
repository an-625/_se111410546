"""校務系統 (School Management System)
Python + Flask + SQLite 網頁版
功能:學生管理 / 教師管理 / 課程管理 / 成績管理 / 出缺勤管理
執行: python app.py 之後用瀏覽器開啟 http://127.0.0.1:5000
"""
import os
import sqlite3
from flask import Flask, g, render_template, request, redirect, url_for, flash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "school.db")

app = Flask(__name__)
app.secret_key = "school-system-2026"


# ---------- 資料庫 ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT DEFAULT '',
            class_name TEXT DEFAULT '',
            phone TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS teachers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            subject TEXT DEFAULT '',
            phone TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            teacher_id TEXT DEFAULT '',
            credit INTEGER DEFAULT 0,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            score REAL NOT NULL,
            UNIQUE(student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            status TEXT NOT NULL,
            UNIQUE(date, student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        );
        """
    )
    db.commit()
    db.close()


# ---------- 首頁 ----------
@app.route("/")
def index():
    db = get_db()
    counts = {
        "students": db.execute("SELECT COUNT(*) c FROM students").fetchone()["c"],
        "teachers": db.execute("SELECT COUNT(*) c FROM teachers").fetchone()["c"],
        "courses": db.execute("SELECT COUNT(*) c FROM courses").fetchone()["c"],
        "grades": db.execute("SELECT COUNT(*) c FROM grades").fetchone()["c"],
        "attendance": db.execute("SELECT COUNT(*) c FROM attendance").fetchone()["c"],
    }
    recent_grades = db.execute(
        """SELECT g.score, s.name AS sname, c.name AS cname
           FROM grades g
           JOIN students s ON s.id = g.student_id
           JOIN courses c ON c.id = g.course_id
           ORDER BY g.id DESC LIMIT 5"""
    ).fetchall()
    return render_template("index.html", counts=counts, recent_grades=recent_grades)


# ---------- 學生管理 ----------
@app.route("/students", methods=["GET", "POST"])
def students():
    db = get_db()
    if request.method == "POST":
        sid = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        if not sid or not name:
            flash("學號和姓名不可空白", "error")
        else:
            try:
                db.execute(
                    "INSERT INTO students(id,name,gender,class_name,phone) VALUES(?,?,?,?,?)",
                    (sid, name, request.form.get("gender", ""),
                     request.form.get("class_name", ""), request.form.get("phone", "")),
                )
                db.commit()
                flash(f"已新增學生 {name}", "ok")
            except sqlite3.IntegrityError:
                flash(f"學號 {sid} 已存在", "error")
        return redirect(url_for("students"))
    q = request.args.get("q", "").strip()
    if q:
        rows = db.execute(
            "SELECT * FROM students WHERE id LIKE ? OR name LIKE ? OR class_name LIKE ? ORDER BY id",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM students ORDER BY id").fetchall()
    return render_template("students.html", rows=rows, q=q)


@app.route("/students/delete/<sid>")
def students_delete(sid):
    db = get_db()
    db.execute("DELETE FROM students WHERE id=?", (sid,))
    db.commit()
    flash(f"已刪除學生 {sid}", "ok")
    return redirect(url_for("students"))


# ---------- 教師管理 ----------
@app.route("/teachers", methods=["GET", "POST"])
def teachers():
    db = get_db()
    if request.method == "POST":
        tid = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        if not tid or not name:
            flash("編號和姓名不可空白", "error")
        else:
            try:
                db.execute(
                    "INSERT INTO teachers(id,name,subject,phone) VALUES(?,?,?,?)",
                    (tid, name, request.form.get("subject", ""), request.form.get("phone", "")),
                )
                db.commit()
                flash(f"已新增教師 {name}", "ok")
            except sqlite3.IntegrityError:
                flash(f"編號 {tid} 已存在", "error")
        return redirect(url_for("teachers"))
    q = request.args.get("q", "").strip()
    if q:
        rows = db.execute(
            "SELECT * FROM teachers WHERE id LIKE ? OR name LIKE ? OR subject LIKE ? ORDER BY id",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM teachers ORDER BY id").fetchall()
    return render_template("teachers.html", rows=rows, q=q)


@app.route("/teachers/delete/<tid>")
def teachers_delete(tid):
    db = get_db()
    db.execute("DELETE FROM teachers WHERE id=?", (tid,))
    db.commit()
    flash(f"已刪除教師 {tid}", "ok")
    return redirect(url_for("teachers"))


# ---------- 課程管理 ----------
@app.route("/courses", methods=["GET", "POST"])
def courses():
    db = get_db()
    if request.method == "POST":
        cid = request.form.get("id", "").strip()
        name = request.form.get("name", "").strip()
        teacher_id = request.form.get("teacher_id", "").strip() or None
        try:
            credit = int(request.form.get("credit", "0") or 0)
        except ValueError:
            credit = 0
        if not cid or not name:
            flash("課程編號和名稱不可空白", "error")
        else:
            try:
                db.execute(
                    "INSERT INTO courses(id,name,teacher_id,credit) VALUES(?,?,?,?)",
                    (cid, name, teacher_id, credit),
                )
                db.commit()
                flash(f"已新增課程 {name}", "ok")
            except sqlite3.IntegrityError:
                flash(f"課程編號 {cid} 已存在(或教師編號錯誤)", "error")
        return redirect(url_for("courses"))
    rows = db.execute(
        """SELECT c.*, t.name AS tname FROM courses c
           LEFT JOIN teachers t ON t.id = c.teacher_id ORDER BY c.id"""
    ).fetchall()
    teacher_list = db.execute("SELECT * FROM teachers ORDER BY id").fetchall()
    return render_template("courses.html", rows=rows, teacher_list=teacher_list)


@app.route("/courses/delete/<cid>")
def courses_delete(cid):
    db = get_db()
    db.execute("DELETE FROM courses WHERE id=?", (cid,))
    db.commit()
    flash(f"已刪除課程 {cid}", "ok")
    return redirect(url_for("courses"))


# ---------- 成績管理 ----------
@app.route("/grades", methods=["GET", "POST"])
def grades():
    db = get_db()
    if request.method == "POST":
        sid = request.form.get("student_id", "").strip()
        cid = request.form.get("course_id", "").strip()
        try:
            score = float(request.form.get("score", ""))
        except (TypeError, ValueError):
            flash("分數必須是數字", "error")
            return redirect(url_for("grades"))
        if not sid or not cid or not (0 <= score <= 100):
            flash("請選學生/課程,分數需在 0~100", "error")
        else:
            try:
                db.execute(
                    """INSERT INTO grades(student_id,course_id,score) VALUES(?,?,?)
                       ON CONFLICT(student_id,course_id) DO UPDATE SET score=excluded.score""",
                    (sid, cid, score),
                )
                db.commit()
                flash("成績已儲存", "ok")
            except sqlite3.IntegrityError:
                flash("學生或課程不存在", "error")
        return redirect(url_for("grades"))
    q = request.args.get("q", "").strip()
    base = """SELECT g.id, g.score, s.id AS sid, s.name AS sname,
                     c.id AS cid, c.name AS cname FROM grades g
              JOIN students s ON s.id = g.student_id
              JOIN courses c ON c.id = g.course_id"""
    if q:
        rows = db.execute(
            base + " WHERE s.name LIKE ? OR c.name LIKE ? OR s.id LIKE ? ORDER BY g.id DESC",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = db.execute(base + " ORDER BY g.id DESC").fetchall()
    avg = db.execute("SELECT AVG(score) a, MAX(score) mx, MIN(score) mn FROM grades").fetchone()
    students_list = db.execute("SELECT * FROM students ORDER BY id").fetchall()
    courses_list = db.execute("SELECT * FROM courses ORDER BY id").fetchall()
    return render_template("grades.html", rows=rows, q=q, avg=avg,
                           students_list=students_list, courses_list=courses_list)


@app.route("/grades/delete/<int:gid>")
def grades_delete(gid):
    db = get_db()
    db.execute("DELETE FROM grades WHERE id=?", (gid,))
    db.commit()
    flash("已刪除該筆成績", "ok")
    return redirect(url_for("grades"))


# ---------- 出缺勤管理 ----------
STATUS = ["出席", "遲到", "請假", "缺席"]


@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    db = get_db()
    if request.method == "POST":
        date = request.form.get("date", "").strip()
        sid = request.form.get("student_id", "").strip()
        cid = request.form.get("course_id", "").strip()
        status = request.form.get("status", "").strip()
        if not date or not sid or not cid or status not in STATUS:
            flash("日期/學生/課程/狀態都要正確填寫", "error")
        else:
            try:
                db.execute(
                    """INSERT INTO attendance(date,student_id,course_id,status) VALUES(?,?,?,?)
                       ON CONFLICT(date,student_id,course_id) DO UPDATE SET status=excluded.status""",
                    (date, sid, cid, status),
                )
                db.commit()
                flash("出缺勤已儲存", "ok")
            except sqlite3.IntegrityError:
                flash("學生或課程不存在", "error")
        return redirect(url_for("attendance"))
    q = request.args.get("q", "").strip()
    base = """SELECT a.id, a.date, a.status, s.id AS sid, s.name AS sname,
                     c.id AS cid, c.name AS cname FROM attendance a
              JOIN students s ON s.id = a.student_id
              JOIN courses c ON c.id = a.course_id"""
    if q:
        rows = db.execute(
            base + " WHERE s.name LIKE ? OR c.name LIKE ? OR a.date LIKE ? ORDER BY a.date DESC, a.id DESC",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        rows = db.execute(base + " ORDER BY a.date DESC, a.id DESC LIMIT 100").fetchall()
    stat = db.execute("SELECT status, COUNT(*) n FROM attendance GROUP BY status").fetchall()
    students_list = db.execute("SELECT * FROM students ORDER BY id").fetchall()
    courses_list = db.execute("SELECT * FROM courses ORDER BY id").fetchall()
    return render_template("attendance.html", rows=rows, q=q, stat=stat,
                           status_list=STATUS, students_list=students_list,
                           courses_list=courses_list)


@app.route("/attendance/delete/<int:aid>")
def attendance_delete(aid):
    db = get_db()
    db.execute("DELETE FROM attendance WHERE id=?", (aid,))
    db.commit()
    flash("已刪除該筆出缺勤", "ok")
    return redirect(url_for("attendance"))


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
