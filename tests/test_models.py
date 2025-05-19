import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import Qt, QModelIndex

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dip import StudentsTableModel, RoomsTableModel

class TestRoomsTableModel(unittest.TestCase):
    @patch('dip.db.execute_query')
    def setUp(self, mock_execute):
        # Мокаем первый вызов для load_data
        mock_execute.return_value = (
            [(101, 1, 3, 2), (102, 1, 3, 3)],
            ['id', 'etazh', 'kol_mest', 'svobodno']
        )
        self.model = RoomsTableModel()
        self.mock_execute = mock_execute

    @patch('dip.db.execute_query')
    def test_update_availability(self, mock_update):
        # Настраиваем mock для update_room_availability
        mock_update.return_value = True
        
        # Мокаем load_data, чтобы он не вызывал реальный запрос
        with patch.object(self.model, 'load_data'):
            # Вызываем тестируемый метод
            result = self.model.update_room_availability('101', -1)
            
            # Проверяем результат
            self.assertTrue(result)
            mock_update.assert_called_once_with(
                "UPDATE rooms SET svobodno = svobodno + %s WHERE id = %s", 
                (-1, '101')
            )

class TestStudentsTableModel(unittest.TestCase):
    @patch('dip.db.execute_query')
    def setUp(self, mock_execute):
        mock_execute.return_value = (
            [(1, 'Иванов Иван', 'М', 20, 2, 'ФИТ', '123', 101)],
            ['id', 'fio', 'pol', 'vozrast', 'kurs', 'fakultet', 'number_phone', 'room_id']
        )
        self.model = StudentsTableModel()
        self.mock_execute = mock_execute

    def test_row_count(self):
        self.assertEqual(self.model.rowCount(), 1)

    def test_column_count(self):
        self.assertEqual(self.model.columnCount(), 8)

    def test_data_display(self):
        index = self.model.index(0, 1)  # Колонка с ФИО
        self.assertEqual(self.model.data(index, Qt.DisplayRole), 'Иванов Иван')

    @patch('dip.db.execute_query')
    def test_add_student(self, mock_execute):
        mock_execute.return_value = ([(2,)], ['id'])
        student = {
            'fio': 'Петров Петр', 'pol': 'М', 'vozrast': 21,
            'kurs': 3, 'fakultet': 'ФИТ', 'number_phone': '456'
        }
        self.assertTrue(self.model.add_student(student))