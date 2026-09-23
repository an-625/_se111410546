"""校務系統 - 純文字選單版
執行: python school_console.py
功能:學生管理 / 教師管理 / 課程管理 / 成績管理 / 出缺勤管理
資料庫:跟網頁版共用同一個 school.db
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "school.db")


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    con = db()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY, name TEXT NOT NULL,
            gender TEXT DEFAULT '', class_name TEXT DEFAULT '', phone TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS teachers (
            id TEXT PRIMARY KEY, name TEXT NOT NULL,
            subject TEXT DEFAULT '', phone TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY, name TEXT NOT NULL,
            teacher_id TEXT DEFAULT '', credit INTEGER DEFAULT 0,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL, course_id TEXT NOT NULL, score REAL NOT NULL,
            UNIQUE(student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, student_id TEXT NOT NULL,
            course_id TEXT NOT NULL, status TEXT NOT NULL,
            UNIQUE(date, student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE);
        """
    )
    con.commit()
    con.close()


def pause():
    input("按 Enter 繼續...")


def menu(title, items):
    print(f"\n===== {title} =====")
    for key, label in items:
        print(f"{key}. {label}")
    return input("請選擇: ").strip()


# ---------- 學生 ----------
def students():
    while True:
        c = menu("學生管理", [("1", "新增學生"), ("2", "查詢學生"),
                              ("3", "顯示全部"), ("4", "刪除學生"), ("0", "回主選單")])
        con = db()
        if c == "1":
            sid = input("學號: ").strip()
            name = input("姓名: ").strip()
            if not sid or not name:
                print("學號和姓名不可空白")
            else:
                try:
                    con.execute("INSERT INTO students VALUES(?,?,?,?,?)",
                                (sid, name, input("性別: ").strip(),
                                 input("班級: ").strip(), input("電話: ").strip()))
                    con.commit()
                    print(f"已新增 {name}")
                except sqlite3.IntegrityError:
                    print(f"學號 {sid} 已存在")
        elif c == "2":
            q = input("關鍵字(學號/姓名/班級): ").strip()
            for r in con.execute(
                    "SELECT * FROM students WHERE id LIKE ? OR name LIKE ? OR class_name LIKE ?",
                    (f"%{q}%", f"%{q}%", f"%{q}%")):
                print(f"{r['id']} {r['name']} {r['gender']} {r['class_name']} {r['phone']}")
        elif c == "3":
            for r in con.execute("SELECT * FROM students ORDER BY id"):
                print(f"{r['id']} {r['name']} {r['gender']} {r['class_name']} {r['phone']}")
        elif c == "4":
            sid = input("要刪除的學號: ").strip()
            con.execute("DELETE FROM students WHERE id=?", (sid,))
            con.commit()
            print(f"已刪除 {sid} (共 {con.total_changes} 筆異動)")
        elif c == "0":
            con.close()
            return
        con.close()
        pause()


# ---------- 教師 ----------
def teachers():
    while True:
        c = menu("教師管理", [("1", "新增教師"), ("2", "查詢教師"),
                              ("3", "顯示全部"), ("4", "刪除教師"), ("0", "回主選單")])
        con = db()
        if c == "1":
            tid = input("編號: ").strip()
            name = input("姓名: ").strip()
            if not tid or not name:
                print("編號和姓名不可空白")
            else:
                try:
                    con.execute("INSERT INTO teachers VALUES(?,?,?,?)",
                                (tid, name, input("科別/專長: ").strip(),
                                 input("電話: ").strip()))
                    con.commit()
                    print(f"已新增 {name}")
                except sqlite3.IntegrityError:
                    print(f"編號 {tid} 已存在")
        elif c == "2":
            q = input("關鍵字(編號/姓名/科別): ").strip()
            for r in con.execute(
                    "SELECT * FROM teachers WHERE id LIKE ? OR name LIKE ? OR subject LIKE ?",
                    (f"%{q}%", f"%{q}%", f"%{q}%")):
                print(f"{r['id']} {r['name']} {r['subject']} {r['phone']}")
        elif c == "3":
            for r in con.execute("SELECT * FROM teachers ORDER BY id"):
                print(f"{r['id']} {r['name']} {r['subject']} {r['phone']}")
        elif c == "4":
            tid = input("要刪除的編號: ").strip()
            con.execute("DELETE FROM teachers WHERE id=?", (tid,))
            con.commit()
            print(f"已刪除 {tid}")
        elif c == "0":
            con.close()
            return
        con.close()
        pause()


# ---------- 課程 ----------
def courses():
    while True:
        c = menu("課程管理", [("1", "新增課程"), ("2", "顯示全部"),
                              ("3", "刪除課程"), ("0", "回主選單")])
        con = db()
        if c == "1":
            cid = input("課程編號: ").strip()
            name = input("課程名稱: ").strip()
            tid = input("授課教師編號(可空白): ").strip() or None
            try:
                credit = int(input("學分: ").strip() or 0)
            except ValueError:
                credit = 0
            if not cid or not name:
                print("編號和名稱不可空白")
            else:
                try:
                    con.execute("INSERT INTO courses VALUES(?,?,?,?)", (cid, name, tid, credit))
                    con.commit()
                    print(f"已新增 {name}")
                except sqlite3.IntegrityError:
                    print("課程編號已存在(或教師編號錯誤)")
        elif c == "2":
            for r in con.execute(
                    """SELECT c.*, t.name tname FROM courses c
                       LEFT JOIN teachers t ON t.id=c.teacher_id ORDER BY c.id"""):
                print(f"{r['id']} {r['name']} 教師:{r['tname'] or '-'} 學分:{r['credit']}")
        elif c == "3":
            cid = input("要刪除的課程編號: ").strip()
            con.execute("DELETE FROM courses WHERE id=?", (cid,))
            con.commit()
            print(f"已刪除 {cid}")
        elif c == "0":
            con.close()
            return
        con.close()
        pause()


# ---------- 成績 ----------
def grades():
    while True:
        c = menu("成績管理", [("1", "登錄成績"), ("2", "查詢成績"),
                              ("3", "顯示全部+統計"), ("4", "刪除成績"), ("0", "回主選單")])
        con = db()
        if c == "1":
            sid = input("學號: ").strip()
            cid = input("課程編號: ").strip()
            try:
                score = float(input("分數(0~100): ").strip())
            except ValueError:
                print("分數必須是數字")
                con.close()
                pause()
                continue
            if not (0 <= score <= 100):
                print("分數需在 0~100")
            else:
                try:
                    con.execute(
                        """INSERT INTO grades(student_id,course_id,score) VALUES(?,?,?)
                           ON CONFLICT(student_id,course_id) DO UPDATE SET score=excluded.score""",
                        (sid, cid, score))
                    con.commit()
                    print("成績已儲存")
                except sqlite3.IntegrityError:
                    print("學生或課程不存在")
        elif c == "2":
            q = input("關鍵字(學生/課程/學號): ").strip()
            for r in con.execute(
                    """SELECT s.name sname, c.name cname, g.score, g.id FROM grades g
                       JOIN students s ON s.id=g.student_id JOIN courses c ON c.id=g.course_id
                       WHERE s.name LIKE ? OR c.name LIKE ? OR s.id LIKE ?""",
                    (f"%{q}%", f"%{q}%", f"%{q}%")):
                print(f"[{r['id']}] {r['sname']} - {r['cname']}: {r['score']}")
        elif c == "3":
            for r in con.execute(
                    """SELECT s.name sname, c.name cname, g.score FROM grades g
                       JOIN students s ON s.id=g.student_id JOIN courses c ON c.id=g.course_id"""):
                print(f"{r['sname']} - {r['cname']}: {r['score']}")
            a = con.execute("SELECT AVG(score) a, MAX(score) mx, MIN(score) mn FROM grades").fetchone()
            print(f"平均:{a['a']:.1f} 最高:{a['mx']} 最低:{a['mn']}" if a["a"] is not None else "尚無成績")
        elif c == "4":
            try:
                gid = int(input("要刪除的成績編號: ").strip())
                con.execute("DELETE FROM grades WHERE id=?", (gid,))
                con.commit()
                print("已刪除")
            except ValueError:
                print("編號必須是數字")
        elif c == "0":
            con.close()
            return
        con.close()
        pause()


# ---------- 出缺勤 ----------
STATUS = ["出席", "遲到", "請假", "缺席"]


def attendance():
    while True:
        c = menu("出缺勤管理", [("1", "點名"), ("2", "查詢紀錄"),
                                ("3", "顯示統計"), ("4", "刪除紀錄"), ("0", "回主選單")])
        con = db()
        if c == "1":
            date = input("日期(YYYY-MM-DD): ").strip()
            sid = input("學號: ").strip()
            cid = input("課程編號: ").strip()
            print("狀態選項:", "/".join(STATUS))
            st = input("狀態: ").strip()
            if st not in STATUS:
                print("狀態錯誤")
            else:
                try:
                    con.execute(
                        """INSERT INTO attendance(date,student_id,course_id,status) VALUES(?,?,?,?)
                           ON CONFLICT(date,student_id,course_id) DO UPDATE SET status=excluded.status""",
                        (date, sid, cid, st))
                    con.commit()
                    print("已儲存")
                except sqlite3.IntegrityError:
                    print("學生或課程不存在")
        elif c == "2":
            q = input("關鍵字(學生/課程/日期): ").strip()
            for r in con.execute(
                    """SELECT a.id, a.date, a.status, s.name sname, c.name cname FROM attendance a
                       JOIN students s ON s.id=a.student_id JOIN courses c ON c.id=a.course_id
                       WHERE s.name LIKE ? OR c.name LIKE ? OR a.date LIKE ?
                       ORDER BY a.date DESC LIMIT 50""",
                    (f"%{q}%", f"%{q}%", f"%{q}%")):
                print(f"[{r['id']}] {r['date']} {r['sname']} - {r['cname']}: {r['status']}")
        elif c == "3":
            for r in con.execute("SELECT status, COUNT(*) n FROM attendance GROUP BY status"):
                print(f"{r['status']}: {r['n']} 筆")
        elif c == "4":
            try:
                aid = int(input("要刪除的紀錄編號: ").strip())
                con.execute("DELETE FROM attendance WHERE id=?", (aid,))
                con.commit()
                print("已刪除")
            except ValueError:
                print("編號必須是數字")
        elif c == "0":
            con.close()
            return
        con.close()
        pause()


def main():
    init_db()
    while True:
        c = menu("校務系統", [("1", "學生管理"), ("2", "教師管理"), ("3", "課程管理"),
                              ("4", "成績管理"), ("5", "出缺勤管理"), ("0", "離開")])
        if c == "1":
            students()
        elif c == "2":
            teachers()
        elif c == "3":
            courses()
        elif c == "4":
            grades()
        elif c == "5":
            attendance()
        elif c == "0":
            print("再見!")
            break
        else:
            print("無效選項")


if __name__ == "__main__":
    main()
