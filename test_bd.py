import psycopg2

connection = psycopg2.connect(
    dbname='postgres',
    user='postgres.okwxukyvivltgexgjlaf',
    password='pqiBU3JavEhOxm6E',
    host='aws-0-eu-north-1.pooler.supabase.com',
    port='6543'
)

cursor = connection.cursor()

# Пример выполнения запроса для добавления записи
try:
    # SQL-запрос для вставки данных
    insert_query = "INSERT INTO author_demo (id, name) VALUES (%s, %s);"
    data_to_insert = (2, 'Comp')
    
    cursor.execute(insert_query, data_to_insert)
    
    # Сохранение изменений
    connection.commit()
    print("Запись успешно добавлена.")
except Exception as e:
    print("Произошла ошибка при добавлении записи:", e)
finally:
    # Закрытие соединения
    cursor.close()
    connection.close()
