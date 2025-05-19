import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dip import AddEditStudentDialog, ZaselRequestDialog

app = QApplication([])

class TestAddEditStudentDialog(unittest.TestCase):
    def test_validation(self):
        dialog = AddEditStudentDialog()
        dialog.fio_edit.setText("Иванов Иван Иванович")
        dialog.fakultet_edit.setText("ФИТ")
        self.assertTrue(dialog._is_valid)

    def test_get_student_data(self):
        dialog = AddEditStudentDialog()
        dialog.fio_edit.setText("Тестов Тест Тестович")
        dialog.pol_combo.setCurrentText("М")
        dialog.vozrast_spin.setValue(20)
        dialog.kurs_spin.setValue(2)
        dialog.fakultet_edit.setText("ФИТ")
        dialog.phone_edit.setText("1234567890")
        
        data = dialog.get_student_data()
        self.assertEqual(data['fio'], "Тестов Тест Тестович")
        self.assertEqual(data['pol'], "М")
        self.assertEqual(data['vozrast'], 20)
        self.assertEqual(data['number_phone'], "1234567890")

class TestZaselRequestDialog(unittest.TestCase):
    @patch('dip.StudentSelectionDialog')
    def test_select_student(self, mock_dialog):
        mock_dialog.return_value.exec.return_value = True
        mock_dialog.return_value.get_selected_student.return_value = {
            'id': '1', 'fio': 'Тест', 'room_id': '101'
        }
        
        dialog = ZaselRequestDialog(MagicMock(), MagicMock())
        dialog.select_student()
        self.assertIn("Тест", dialog.student_label.text())