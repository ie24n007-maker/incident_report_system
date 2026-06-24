def send_mail(date, title, detail):

    print("===== 重大事故通知 =====")

    print(f"発生日: {date}")

    print(f"件名: {title}")

    print(f"詳細: {detail}")

    print("======================")

from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)
def send_mail(date, title, detail):

    print("===== 重大事故通知 =====")

    print(f"発生日: {date}")

    print(f"件名: {title}")

    print(f"詳細: {detail}")

    print("======================")

# データベース作成
def init_db():
    conn = sqlite3.connect("incidents.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS incidents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        title TEXT,
        level TEXT,
        detail TEXT
    )
    """)

    conn.commit()
    conn.close()


# 一覧表示
@app.route("/")
def index():

    conn = sqlite3.connect("incidents.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM incidents")

    incidents = cur.fetchall()

    conn.close()

    return render_template(
        "index.html",
        incidents=incidents
    )


# 登録
@app.route("/add", methods=["GET", "POST"])
def add():

    if request.method == "POST":

        date = request.form["date"]

        title = request.form["title"]

        level = request.form["level"]

        detail = request.form["detail"]

        conn = sqlite3.connect("incidents.db")

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO incidents
            (date,title,level,detail)

            VALUES(?,?,?,?)
            """,

            (date, title, level, detail)
        )

        conn.commit()

        conn.close()

        if level == "重大":

            send_mail(date, title, detail)

        return redirect("/")

    return render_template("add.html")


# 編集
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    conn = sqlite3.connect("incidents.db")

    cur = conn.cursor()

    if request.method == "POST":

        date = request.form["date"]

        title = request.form["title"]

        level = request.form["level"]

        detail = request.form["detail"]

        cur.execute(
            """
            UPDATE incidents

            SET
            date=?,
            title=?,
            level=?,
            detail=?

            WHERE id=?
            """,

            (date, title, level, detail, id)
        )

        conn.commit()

        conn.close()

        return redirect("/")

    cur.execute(
        "SELECT * FROM incidents WHERE id=?",
        (id,)
    )

    incident = cur.fetchone()

    conn.close()

    return render_template(
        "edit.html",
        incident=incident
    )


# 削除
@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("incidents.db")

    cur = conn.cursor()

    cur.execute(
        "DELETE FROM incidents WHERE id=?",
        (id,)
    )

    conn.commit()

    conn.close()

    return redirect("/")


if __name__ == "__main__":

    init_db()

    app.run(debug=True)