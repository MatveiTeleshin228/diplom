import psycopg2

try:
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres.okwxukyvivltgexgjlaf',
        password='pqiBU3JavEhOxm6E',
        host='aws-0-eu-north-1.pooler.supabase.com',
        port='6543'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    print("Подключение успешно!")
    conn.close()
except Exception as e:
    print(f"Ошибка подключения: {e}")