import sqlite3
from typing import Optional

DB_FILE = "bookstore.db"

def conn_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db(conn: sqlite3.Connection) -> None: 
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS member (
        mid TEXT PRIMARY KEY,
        mname TEXT NOT NULL,
        mphone TEXT NOT NULL,
        memail TEXT
    );

    CREATE TABLE IF NOT EXISTS book (
        bid TEXT PRIMARY KEY,
        btitle TEXT NOT NULL,
        bprice INTEGER NOT NULL,
        bstock INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sale (
        sid INTEGER PRIMARY KEY AUTOINCREMENT,
        sdate TEXT NOT NULL,
        mid TEXT NOT NULL,
        bid TEXT NOT NULL,
        sqty INTEGER NOT NULL,
        sdiscount INTEGER NOT NULL,
        stotal INTEGER NOT NULL
    );

    INSERT OR IGNORE INTO member VALUES 
    ('M001', 'Alice', '0912-345678', 'alice@example.com'),
    ('M002', 'Bob', '0923-456789', 'bob@example.com'),
    ('M003', 'Cathy', '0934-567890', 'cathy@example.com');

    INSERT OR IGNORE INTO book VALUES 
    ('B001', 'Python Programming', 600, 50),
    ('B002', 'Data Science Basics', 800, 30),
    ('B003', 'Machine Learning Guide', 1200, 20);

    INSERT OR IGNORE INTO sale (sid, sdate, mid, bid, sqty, sdiscount, stotal) VALUES
    (1, '2024-01-15', 'M001', 'B001', 2, 100, 1100),
    (2, '2024-01-16', 'M002', 'B002', 1, 50, 750),
    (3, '2024-01-17', 'M001', 'B003', 3, 200, 3400),
    (4, '2024-01-18', 'M003', 'B001', 1, 0, 600);
    """)
    conn.commit()

def add_s(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    sdate = input("請輸入銷售日期 (YYYY-MM-DD)：").strip()
    if len(sdate) != 10 or sdate.count("-") != 2:
        print("=> 日期格式錯誤，請輸入 (YYYY-MM-DD)")
        return

    mid = input("請輸入會員編號：").strip()
    bid = input("請輸入書籍編號：").strip()
    
    try:
        sqty = int(input("請輸入購買數量："))
    except ValueError:
        print("=> 錯誤：數量或折扣必須為整數，請重新輸入")
        return

    if sqty <= 0:
        print("=> 錯誤：數量必須為正整數，請重新輸入")
        return

    try:
        sdiscount = int(input("輸入折扣金額："))
    except ValueError:
        print("=> 錯誤：折扣金額不能為負數，請重新輸入")
        return
    
    cursor.execute("SELECT * FROM member WHERE mid = ?", (mid,))
    member = cursor.fetchone()
    cursor.execute("SELECT * FROM book WHERE bid = ?", (bid,))
    book = cursor.fetchone()
    
    if not book or not member:
        print("=> 錯誤：會員編號或書籍編號無效")
        return
    
    if book["bstock"] < sqty:
        print(f"=> 錯誤：書籍庫存不足 (現有庫存: {book['bstock']})")
        return

    bprice = book["bprice"]
    stotal = bprice * sqty - sdiscount

    try:
        cursor.execute(
            "INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal) VALUES (?, ?, ?, ?, ?, ?)",
            (sdate, mid, bid, sqty, sdiscount, stotal)
        )
        cursor.execute(
            "UPDATE book SET bstock = bstock - ? WHERE bid = ?",
            (sqty, bid)
        )
        conn.commit()
        print(f"=> 銷售記錄已新增！(銷售總額: {stotal:,})")
    except sqlite3.Error:
        conn.rollback()
        print("=> 錯誤：新增記錄失敗")

def s_report(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.sid, s.sdate, m.mname, b.btitle, b.bprice, s.sqty, s.sdiscount, s.stotal
        FROM sale s
        JOIN member m ON s.mid = m.mid
        JOIN book b ON s.bid = b.bid
        ORDER BY s.sid
    """)
    sales = cursor.fetchall()

    print("\n==================== 銷售報表 ====================")
    for idx, row in enumerate(sales, start=1):
        print(f"銷售 #{idx}")
        print(f"銷售編號: {row['sid']}")
        print(f"銷售日期: {row['sdate']}")
        print(f"會員姓名: {row['mname']}")
        print(f"書籍標題: {row['btitle']}")
        print("--------------------------------------------------")
        print("單價\t數量\t折扣\t小計")
        print("--------------------------------------------------")
        print(f"{row['bprice']}\t{row['sqty']}\t{row['sdiscount']}\t{row['stotal']:,}")
        print("--------------------------------------------------")
        print(f"銷售總額: {row['stotal']:,}")
        print("==================================================\n")

def update_s(conn: sqlite3.Connection) -> None:
    """更新銷售折扣金額與總額"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.sid, s.sdate, m.mname, b.bprice, s.sqty
        FROM sale s
        JOIN member m ON s.mid = m.mid
        JOIN book b ON s.bid = b.bid
        ORDER BY s.sid
    """)
    sales = cursor.fetchall()

    if not sales:
        print("=> 無銷售資料")
        return

    print("\n======== 銷售記錄列表 ========")
    for idx, row in enumerate(sales, start=1):
        print(f"{idx}. 銷售編號: {row['sid']} - 會員: {row['mname']} - 日期: {row['sdate']}")
    print("================================")

    try:
        choice = input("請選擇要更新的銷售編號 (輸入數字或按 Enter 取消): ").strip()
        if not choice:
            return
        idx = int(choice)
        if idx < 1 or idx > len(sales):
            raise ValueError
    except ValueError:
        print("=> 錯誤：請輸入有效的數字")
        return

    sid = sales[idx - 1]["sid"]
    bprice = sales[idx - 1]["bprice"]
    sqty = sales[idx - 1]["sqty"]

    try:
        discount = int(input("請輸入新的折扣金額："))
        if discount < 0:
            raise ValueError
    except ValueError:
        print("=> 錯誤：折扣金額不能為負數")
        return

    total = bprice * sqty - discount
    cursor.execute(
        "UPDATE sale SET sdiscount = ?, stotal = ? WHERE sid = ?",
        (discount, total, sid)
    )
    conn.commit()
    print(f"=> 銷售編號 {sid} 已更新！(銷售總額: {total:,})")

def main():

    with conn_db() as conn:
        initialize_db(conn)

        while True:
            print("***************選單***************")
            print("1. 新增銷售記錄")
            print("2. 顯示銷售報表")
            print("3. 更新銷售紀錄")
            print("4. 刪除銷售紀錄")
            print("5. 離開\n")
            print("**********************************")
            choice = input("請選擇操作項目(Enter 離開)： ").strip()
            
            if choice == "1":
                add_s(conn)
            elif choice == "2":
                s_report(conn)
            elif choice == "3":
                update_s(conn)
            elif choice == "4":
                ()
            elif choice == "5":
                break
            else:
                print("=> 請輸入有效的選項（1-5）")

if __name__ == "__main__":
    main()
