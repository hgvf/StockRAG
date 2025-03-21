import psycopg2

def clear():
    """
    Clear the content of DB
        TW_HistoryLog, TW_MomentumInfo, TW_MomentumDataHistory
    """

    conn = psycopg2.connect(
        dbname="stock_db",
        user="weiwei",
        password="weiwei",
        host="db",
        port="5432"
    )
    cur = conn.cursor()

    cur.execute("""
                DELETE FROM TW_MomentumDataHistory;
            """)
    conn.commit()

    cur.execute("""
                DELETE FROM TW_MomentumInfo;
            """)
    conn.commit()

    cur.execute("""
                DELETE FROM TW_HistoryLog;
            """)
    conn.commit()

    cur.execute("""
                DELETE FROM EXE_history;
            """)
    conn.commit()