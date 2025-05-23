import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import Qt, QModelIndex, QItemSelectionModel

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dip import StudentsWidget, RoomsWidget, StudentsTableModel, RoomsTableModel, QSortFilterProxyModel

class TestStudentsWidget(unittest.TestCase):
    def setUp(self):
        self.real_model = StudentsTableModel()
        
        with patch.object(self.real_model, 'load_data'):
            self.proxy_model = QSortFilterProxyModel()
            self.proxy_model.setSourceModel(self.real_model)
            self.widget = StudentsWidget()
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

    @patch.object(StudentsTableModel, 'remove_student')
    def test_delete_student_button(self, mock_remove):
        mock_remove.return_value = True
        
        # Создаем корректный mock для индекса
        mock_index = MagicMock()
        mock_index.row.return_value = 0  # Возвращаем конкретное число
        
        mock_proxy_index = MagicMock()
        
        # Мокаем proxy_model
        mock_proxy_model = MagicMock()
        mock_proxy_model.mapToSource.return_value = mock_index
        self.widget.proxy_model = mock_proxy_model
        
        # Мокаем selectionModel
        mock_selection = MagicMock()
        mock_selection.selectedRows.return_value = [mock_proxy_index]
        self.widget.table_view.selectionModel = MagicMock(return_value=mock_selection)
        
        # Мокаем can_delete_student
        with patch.object(self.widget.students_model, 'can_delete_student', return_value=True):
            self.widget.delete_student()
            mock_remove.assert_called_once()

class TestRoomsWidget(unittest.TestCase):
    def setUp(self):
        self.real_model = RoomsTableModel()
        
        with patch.object(self.real_model, 'load_data'):
            self.proxy_model = QSortFilterProxyModel()
            self.proxy_model.setSourceModel(self.real_model)
            self.widget = RoomsWidget()
            self.widget.rooms_model = self.real_model
            self.widget.proxy_model = self.proxy_model
            self.widget.table.setModel(self.proxy_model)

    @patch('dip.db.execute_query')
    def test_show_room_students(self, mock_execute):
        mock_execute.return_value = ([(1, 3, 1)], ['etazh', 'kol_mest', 'svobodno'])
        
        mock_selection = MagicMock()
        mock_index = MagicMock()
        mock_index.row.return_value = 0
        mock_selection.selectedRows.return_value = [mock_index]
        self.widget.table.selectionModel = MagicMock(return_value=mock_selection)
        
        self.widget.proxy_model.mapToSource = MagicMock(return_value=MagicMock(row=MagicMock(return_value=0)))
        
        self.widget.show_room_students()
        self.assertIn("Комната", self.widget.students_list.text())

    def test_filter_rooms_by_id(self):
        test_text = "101"
        self.widget.filter_edit.setText(test_text)
        
        with patch.object(self.widget.proxy_model, 'setFilterFixedString') as mock_filter:
            self.widget.filter_edit.textChanged.emit(test_text)
            mock_filter.assert_called_once_with(test_text)