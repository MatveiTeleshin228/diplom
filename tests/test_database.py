import unittest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dip import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database()
        
    @patch('psycopg2.connect')
    def test_connect_success(self, mock_connect):
        """Тест успешного подключения к базе данных"""
        mock_connect.return_value.closed = False
        self.db.connect()
        self.assertIsNotNone(self.db.connection)
        
    @patch('psycopg2.connect')
    def test_connect_failure(self, mock_connect):
        """Тест неудачного подключения к базе данных"""
        mock_connect.side_effect = Exception("Connection error")
        with self.assertRaises(Exception):
            self.db.connect()
                
    @patch('psycopg2.connect')
    def test_execute_query_success(self, mock_connect):
        """Тест успешного выполнения запроса"""
        mock_conn = mock_connect.return_value
        mock_conn.closed = False
        mock_cursor = mock_conn.cursor.return_value
        
        # Исправляем описание колонки - теперь оно соответствует реальному поведению
        mock_cursor.description = [('?column?',)]
        mock_cursor.fetchall.return_value = [(1,)]
        
        result, columns = self.db.execute_query("SELECT 1", fetch=True)
        self.assertEqual(result, [(1,)])
        self.assertEqual(columns, ['?column?'])  # Ожидаем именно такое имя колонки
                
    def tearDown(self):
        if hasattr(self.db, 'connection') and self.db.connection:
            self.db.connection.close()