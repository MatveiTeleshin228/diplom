import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import Qt, QModelIndex, QItemSelectionModel
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dip import StudentsWidget, RoomsWidget, StudentsTableModel, RoomsTableModel, QSortFilterProxyModel

# Глобальная QApplication
app = QApplication.instance() or QApplication([])

class TestStudentsWidget(unittest.TestCase):
    def setUp(self):
        # Создаем реальную модель студентов
        self.real_model = StudentsTableModel()
        
        # Мокаем загрузку данных
        with patch.object(self.real_model, 'load_data'):
            # Создаем прокси-модель
            self.proxy_model = QSortFilterProxyModel()
            self.proxy_model.setSourceModel(self.real_model)
            
            # Создаем виджет
            self.widget = StudentsWidget()
            
            # Подменяем модели в виджете
            self.widget.students_model = self.real_model
            self.widget.proxy_model = self.proxy_model
            self.widget.table_view.setModel(self.proxy_model)

    @patch('dip.AddEditStudentDialog')
    @patch.object(StudentsTableModel, 'add_student')
    def test_add_student(self, mock_add_student, mock_dialog):
        mock_dialog.return_value.exec.return_value = True
        mock_dialog.return_value.get_student_data.return_value = {
            'fio': 'Новый Студент', 'pol': 'М', 'vozrast': 20,
            'kurs': 1, 'fakultet': 'ФИТ', 'number_phone': '789'
        }
        mock_add_student.return_value = True
        
        self.widget.add_student()
        mock_add_student.assert_called_once()

class TestRoomsWidget(unittest.TestCase):
    def setUp(self):
        # Создаем реальную модель комнат
        self.real_model = RoomsTableModel()
        
        # Мокаем загрузку данных
        with patch.object(self.real_model, 'load_data'):
            # Создаем прокси-модель
            self.proxy_model = QSortFilterProxyModel()
            self.proxy_model.setSourceModel(self.real_model)
            
            # Создаем виджет
            self.widget = RoomsWidget()
            
            # Подменяем модели в виджете
            self.widget.rooms_model = self.real_model
            self.widget.proxy_model = self.proxy_model
            self.widget.table.setModel(self.proxy_model)
            
            # Мокаем selectionModel
            self.mock_selection = MagicMock()
            self.widget.table.selectionModel = MagicMock(return_value=self.mock_selection)

    @patch('dip.db.execute_query')
    def test_show_room_students(self, mock_execute):
        mock_execute.return_value = ([(1, 3, 1)], ['etazh', 'kol_mest', 'svobodno'])
        
        # Имитируем выбор строки
        mock_index = MagicMock()
        mock_index.row.return_value = 0
        self.mock_selection.selectedRows.return_value = [mock_index]
        
        # Мокаем mapToSource
        self.proxy_model.mapToSource = MagicMock(return_value=MagicMock(row=MagicMock(return_value=0)))
        
        # Вызываем тестируемый метод
        self.widget.show_room_students()
        
        # Проверяем результат
        self.assertIn("Комната", self.widget.students_list.text())