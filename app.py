from flask import Flask, render_template, request, redirect
import psycopg2
from psycopg2.extras import DictCursor
import webbrowser

app = Flask(__name__)

# 🔑 【重要】ここにSupabaseの接続URL（接続文字列）を貼り付けます！
# 例: "postgresql://postgres.xxxx:password@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
SUPABASE_DATABASE_URL = "postgresql://postgres.kcfrxsdveasqeefegvga:grueaogkobvjnfdsbrd@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

# クラウドDBに接続するための共通関数
def get_db_connection():
    # sqlite3.connect の代わりにクラウドのURLで接続
    # DictCursorを使うことで、sqliteのようにカラム名でデータを扱いやすくします
    conn = psycopg2.connect(SUPABASE_DATABASE_URL, cursor_factory=DictCursor)
    return conn

# 重大事故時の通知ロジック
def send_mail(date, location, title, detail):
    print("\n===== ⚠️ 重大事故通知 =====")
    print(f"発生日: {date}")
    print(f"場所 : {location}")
    print(f"件名 : {title}")
    print(f"詳細 : {detail}")
    print("==========================\n")

# データベース初期化（クラウド上にテーブルがなければ作成）
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # PostgreSQLの文法に合わせて、AUTOINCREMENT を SERIAL に変更しています
    cur.execute("""
    CREATE TABLE IF NOT EXISTS incidents(
        id SERIAL PRIMARY KEY,
        date TEXT,
        location TEXT,
        title TEXT,
        level TEXT,
        detail TEXT
    )
    """)
    conn.commit()
    cur.close()
    conn.close()

# 一覧表示（ソート機能 ＆ 繰り返し検出付き）
@app.route("/")
def index():
    sort_by = request.args.get("sort", "date_desc")
    
    conn = get_db_connection()
    cur = conn.cursor()

    if sort_by == "date_asc":
        cur.execute("SELECT * FROM incidents ORDER BY date ASC")
    elif sort_by == "level_desc":
        cur.execute("""
            SELECT * FROM incidents 
            ORDER BY CASE level WHEN '重大' THEN 1 WHEN '中' THEN 2 ELSE 3 END ASC
        """)
    else:
        cur.execute("SELECT * FROM incidents ORDER BY date DESC")
        
    incidents = cur.fetchall()

    # 繰り返し発生しているインシデント（PostgreSQLではCOUNT(*)に別名をつけた場合、HAVINGでもそれを使います）
    cur.execute("""
        SELECT title, COUNT(*) as occurrence_count 
        FROM incidents 
        GROUP BY title 
        HAVING COUNT(*) >= 2
    """)
    repeated_incidents = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        incidents=incidents,
        repeated_incidents=repeated_incidents,
        current_sort=sort_by
    )

# 新規登録
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        date = request.form["date"]
        location = request.form["location"]
        title = request.form["title"]
        level = request.form["level"]
        detail = request.form["detail"]

        conn = get_db_connection()
        cur = conn.cursor()
        # SQL文の中の「?」は、PostgreSQLでは「%s」に変わります
        cur.execute(
            """
            INSERT INTO incidents (date, location, title, level, detail)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (date, location, title, level, detail)
        )
        conn.commit()
        cur.close()
        conn.close()

        if level == "重大":
            send_mail(date, location, title, detail)

        return redirect("/")

    return render_template("add.html")

# 編集
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        date = request.form["date"]
        location = request.form["location"]
        title = request.form["title"]
        level = request.form["level"]
        detail = request.form["detail"]

        cur.execute(
            """
            UPDATE incidents
            SET date=%s, location=%s, title=%s, level=%s, detail=%s
            WHERE id=%s
            """,
            (date, location, title, level, detail, id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/")

    cur.execute("SELECT * FROM incidents WHERE id=%s", (id,))
    incident = cur.fetchone()
    cur.close()
    conn.close()

    return render_template("edit.html", incident=incident)

# 削除
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM incidents WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    # アプリ起動時にSupabase側をチェック・初期化
    # 💡 最初に誰か1人が起動した時点でクラウド側にテーブルが自動作成されます！
    init_db()
    
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)