import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QPlainTextEdit, QMessageBox

from dip import AddEditStudentDialog, ZaselRequestDialog, LogViewerDialog

@pytest.mark.usefixtures("qapp")
class TestAddEditStudentDialog:
    def test_validation(self, qapp):
        dialog = AddEditStudentDialog()
        dialog.fio_edit.setText("Иванов Иван Иванович")
        dialog.fakultet_edit.setText("ФИТ")
        assert dialog._is_valid is True

    def test_get_student_data(self, qapp):
        dialog = AddEditStudentDialog()
        # Заполняем данные
        dialog.fio_edit.setText("Тестов Тест Тестович")
        dialog.pol_combo.setCurrentText("М")
        dialog.vozrast_spin.setValue(20)
        dialog.kurs_spin.setValue(2)
        dialog.fakultet_edit.setText("ФИТ")
        dialog.phone_edit.setText("1234567890")
        
        data = dialog.get_student_data()
        assert data['fio'] == "Тестов Тест Тестович"
        assert data['pol'] == "М"
        assert data['vozrast'] == 20
        assert data['number_phone'] == "1234567890"

@pytest.mark.usefixtures("qapp")        
class TestZaselRequestDialog:
    @patch('dip.StudentSelectionDialog')
    def test_select_student(self, mock_dialog, qapp):
        mock_dialog.return_value.exec.return_value = True
        mock_dialog.return_value.get_selected_student.return_value = {
            'id': '1', 'fio': 'Тест', 'room_id': '101'
        }
        
        dialog = ZaselRequestDialog(MagicMock(), MagicMock())
        dialog.select_student()
        assert "Тест" in dialog.student_label.text()

@pytest.mark.usefixtures("qapp")
class TestLogViewerDialog:
    @pytest.fixture(autouse=True)
    def setup(self, qapp):
        self.dialog = LogViewerDialog()
        self.dialog.text_edit = QPlainTextEdit()

    @patch('builtins.open')
    def test_load_logs_utf8(self, mock_open, qapp):
        mock_file = MagicMock()
        mock_file.__enter__.return_value.readlines.return_value = [
            "2023-01-01 INFO: Всё ок\n",
            "2023-01-02 ERROR: Упало всё\n"
        ]
        mock_open.return_value = mock_file
        
        self.dialog.load_logs()
        assert "Упало всё" in self.dialog.text_edit.toPlainText()

    @patch('builtins.open')
    def test_load_logs_cp1251(self, mock_open):
        """Тест загрузки логов в CP-1251, если UTF-8 не сработал"""
        # Настраиваем два разных поведения для open
        mock_file_utf8 = MagicMock()
        mock_file_utf8.__enter__.side_effect = UnicodeDecodeError('utf-8', b'', 0, 1, 'Test')
        
        mock_file_cp1251 = MagicMock()
        mock_file_cp1251.__enter__.return_value.readlines.return_value = [
            "2023-01-01 INFO: Кодировка CP-1251\n"
        ]
        
        mock_open.side_effect = [mock_file_utf8, mock_file_cp1251]
        
        self.dialog.load_logs()
        assert "CP-1251" in self.dialog.text_edit.toPlainText()
        
    @patch('builtins.open')
    def test_clear_logs(self, mock_open, qapp):
        mock_file = MagicMock()
        mock_open.return_value = mock_file
        
        with patch('dip.QMessageBox.question', return_value=QMessageBox.Yes):
            self.dialog.clear_logs()
            mock_file.__enter__.return_value.write.assert_called_once_with("")