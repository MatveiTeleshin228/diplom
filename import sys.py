import sys
import re
import logging
import time

from PySide6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QThreadPool,
    QRunnable,
    QObject,
    Signal,
    QPropertyAnimation,
    QEasingCurve,
    QRegularExpression,
    QSortFilterProxyModel,
)
from PySide6.QtGui import QFont, QAction, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QDialog,
    QFormLayout,
    QComboBox,
    QTabWidget,
    QProgressDialog,
    QHeaderView,
    QGraphicsOpacityEffect,
    QSpinBox,
    QSizePolicy,
    QPlainTextEdit,
)

# Подробное логирование
logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    filemode="a",
    format="%(asctime)s %(levelname)s: %(message)s",
)


def exception_hook(exc_type, exc_value, exc_traceback):
    logging.error(
        "Неперехваченное исключение", exc_info=(exc_type, exc_value, exc_traceback)
    )
    if QApplication.instance():
        QMessageBox.critical(
            None,
            "Критическая ошибка",
            "Произошла непредвиденная ошибка. Приложение будет закрыто.",
        )
    else:
        print(
            "Критическая ошибка: Произошла непредвиденная ошибка. Приложение будет закрыто.",
            file=sys.stderr,
        )
    sys.exit(1)


sys.excepthook = exception_hook

# QSS-стилизация приложения
APP_QSS = """
QMainWindow {
    background-color: #f0f0f0;
}

QTabWidget::pane {
    border: 1px solid #C2C7CB;
    background: #ffffff;
}

QTabBar::tab {
    background: #e0e0e0;
    padding: 10px;
    margin: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background: #ffffff;
    border-bottom: 2px solid #3498db;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #2980b9;
}
QPushButton:pressed {
    background-color: #1c5980;
}

QLineEdit, QComboBox, QSpinBox {
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    padding: 4px;
    background-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #3498db;
}

QTableView {
    background-color: #ffffff;
    gridline-color: #bdc3c7;
}
QHeaderView::section {
    background-color: #ecf0f1;
    padding: 4px;
    border: 1px solid #bdc3c7;
}
"""


# Окно просмотра логов
class LogViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Просмотр логов")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_logs)
        layout.addWidget(refresh_button)
        self.load_logs()

    def load_logs(self):
        try:
            with open("app.log", "r", encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
        except Exception as e:
            self.text_edit.setPlainText("Ошибка чтения лог файла: " + str(e))


# Модель для списка студентов с явным маппингом колонок
class StudentsTableModel(QAbstractTableModel):
    HEADERS = ["ID", "ФИО", "Пол", "Возраст", "Курс", "Факультет"]

    def __init__(self, students=None):
        super().__init__()
        self._students = students or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._students)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        student = self._students[index.row()]
        if role == Qt.DisplayRole:
            mapping = {
                "ID": "id",
                "ФИО": "fio",
                "Пол": "pol",
                "Возраст": "vozrast",
                "Курс": "kurs",
                "Факультет": "fakultet",
            }
            header = self.HEADERS[index.column()]
            return student.get(mapping.get(header, ""), "")
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    def add_student(self, student):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._students.append(student)
        self.endInsertRows()
        logging.info("Добавлен студент: %s", student)

    def update_student(self, row, student):
        if 0 <= row < len(self._students):
            self._students[row] = student
            index1 = self.index(row, 0)
            index2 = self.index(row, self.columnCount() - 1)
            self.dataChanged.emit(index1, index2)
            logging.info("Обновлен студент в строке %d: %s", row, student)

    def remove_student(self, row):
        if 0 <= row < len(self._students):
            self.beginRemoveRows(QModelIndex(), row, row)
            student = self._students.pop(row)
            self.endRemoveRows()
            logging.info("Удалён студент: %s", student)

    def get_student(self, row):
        if 0 <= row < len(self._students):
            return self._students[row]
        return None


# Модель для списка комнат с явным маппингом колонок
class RoomsTableModel(QAbstractTableModel):
    HEADERS = ["ID", "Этаж", "Кол-во мест", "Свободно"]

    def __init__(self, rooms=None):
        super().__init__()
        self._rooms = rooms or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._rooms)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        room = self._rooms[index.row()]
        if role == Qt.DisplayRole:
            mapping = {
                "ID": "id",
                "Этаж": "etazh",
                "Кол-во мест": "kol_mest",
                "Свободно": "svobodno",
            }
            header = self.HEADERS[index.column()]
            return room.get(mapping.get(header, ""), "")
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None


# Модель для заявок с расширенным набором колонок и явным маппингом
class RequestsTableModel(QAbstractTableModel):
    HEADERS = ["ID", "Тип заявки", "Статус", "Студент", "Комната"]

    def __init__(self, requests=None):
        super().__init__()
        self._requests = requests or []

    def rowCount(self, parent=QModelIndex()):
        return len(self._requests)

    def columnCount(self, parent=QModelIndex()):
        return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        request = self._requests[index.row()]
        if role == Qt.DisplayRole:
            mapping = {
                "ID": "id",
                "Тип заявки": "type",
                "Статус": "status",
                "Студент": "student_fio",
                "Комната": "room_id",
            }
            header = self.HEADERS[index.column()]
            return request.get(mapping.get(header, ""), "")
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    def add_request(self, request):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._requests.append(request)
        self.endInsertRows()
        logging.info("Добавлена заявка: %s", request)


# Прокси-модель для расширенной фильтрации студентов
class StudentsProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_text = ""

    def setFilterText(self, text):
        self.filter_text = text
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filter_text.strip():
            return True
        reg_ex = QRegularExpression(
            self.filter_text, QRegularExpression.CaseInsensitiveOption
        )
        source_model = self.sourceModel()
        for col in range(source_model.columnCount()):
            index = source_model.index(source_row, col, source_parent)
            data = source_model.data(index, Qt.DisplayRole)
            if data is None:
                continue
            if reg_ex.isValid() and reg_ex.match(str(data)).hasMatch():
                return True
            elif self.filter_text.lower() in str(data).lower():
                return True
        return False


# Диалог добавления/редактирования студента с использованием QSpinBox
class AddEditStudentDialog(QDialog):
    def __init__(self, parent=None, student_data=None):
        super().__init__(parent)
        self.setWindowTitle(
            "Добавить студента" if student_data is None else "Редактировать студента"
        )
        self.setModal(True)
        self._is_valid = False

        layout = QFormLayout(self)
        self.fio_edit = QLineEdit()
        self.fio_edit.setPlaceholderText("Введите ФИО")
        self.fio_edit.textChanged.connect(self.validate_inputs)

        self.pol_combo = QComboBox()
        self.pol_combo.addItems(["М", "Ж"])

        self.vozrast_spin = QSpinBox(self)
        self.vozrast_spin.setRange(16, 100)
        self.vozrast_spin.valueChanged.connect(self.validate_inputs)

        self.kurs_spin = QSpinBox(self)
        self.kurs_spin.setRange(1, 6)
        self.kurs_spin.valueChanged.connect(self.validate_inputs)

        self.fakultet_edit = QLineEdit()
        self.fakultet_edit.setPlaceholderText("Введите факультет")
        self.fakultet_edit.textChanged.connect(self.validate_inputs)

        layout.addRow("ФИО:", self.fio_edit)
        layout.addRow("Пол:", self.pol_combo)
        layout.addRow("Возраст:", self.vozrast_spin)
        layout.addRow("Курс:", self.kurs_spin)
        layout.addRow("Факультет:", self.fakultet_edit)

        button_layout = QHBoxLayout()
        self.ok_button = AnimatedButton("ОК")
        self.ok_button.clicked.connect(self.on_ok)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

        fio_validator = QRegularExpressionValidator(
            QRegularExpression(r"^[А-ЯЁ][а-яё]+(\s[А-ЯЁ][а-яё]+){2}$"), self
        )
        self.fio_edit.setValidator(fio_validator)

        if student_data:
            self.fio_edit.setText(student_data.get("fio", ""))
            index = self.pol_combo.findText(student_data.get("pol", "М"))
            if index >= 0:
                self.pol_combo.setCurrentIndex(index)
            self.vozrast_spin.setValue(int(student_data.get("vozrast", 16)))
            self.kurs_spin.setValue(int(student_data.get("kurs", 1)))
            self.fakultet_edit.setText(student_data.get("fakultet", ""))
        self.validate_inputs()

    def validate_inputs(self):
        valid = True
        if not self.fio_edit.text().strip():
            self.fio_edit.setStyleSheet("border: 1px solid red;")
            valid = False
        else:
            self.fio_edit.setStyleSheet("")
        if not self.fakultet_edit.text().strip():
            self.fakultet_edit.setStyleSheet("border: 1px solid red;")
            valid = False
        else:
            self.fakultet_edit.setStyleSheet("")
        self._is_valid = valid
        self.ok_button.setEnabled(valid)

    def on_ok(self):
        if self._is_valid:
            self.accept()
        else:
            QMessageBox.warning(
                self, "Ошибка", "Заполните обязательные поля корректно."
            )

    def get_student_data(self):
        return {
            "id": "0",
            "fio": self.fio_edit.text().strip(),
            "pol": self.pol_combo.currentText(),
            "vozrast": self.vozrast_spin.value(),
            "kurs": self.kurs_spin.value(),
            "fakultet": self.fakultet_edit.text().strip(),
        }


# Кастомная кнопка с анимацией прозрачности
class AnimatedButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(150)
        self.animation.setStartValue(0.7)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.clicked.connect(self.start_animation)

    def start_animation(self):
        self.animation.start()


# Диалог создания заявки на заселение с выбором студента и комнаты
class ZaselRequestDialog(QDialog):
    def __init__(self, student_model, room_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать заявку на заселение")
        self.student_model = student_model
        self.room_model = room_model
        layout = QFormLayout(self)
        self.student_combo = QComboBox(self)
        for i in range(student_model.rowCount()):
            student = student_model._students[i]
            display = f"{student.get('id')} - {student.get('fio')}"
            self.student_combo.addItem(display, student)
        self.room_combo = QComboBox(self)
        for room in room_model._rooms:
            try:
                if int(room.get("svobodno", "0")) > 0:
                    display = f"{room.get('id')} - Этаж: {room.get('etazh')}, Мест: {room.get('kol_mest')}, Свободно: {room.get('svobodno')}"
                    self.room_combo.addItem(display, room)
            except Exception:
                continue
        layout.addRow("Студент:", self.student_combo)
        layout.addRow("Комната:", self.room_combo)
        button_layout = QHBoxLayout()
        ok_button = AnimatedButton("ОК")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

    def get_request_data(self):
        student = self.student_combo.currentData()
        room = self.room_combo.currentData()
        return {
            "id": "",
            "type": "Заселение",
            "status": "Создана",
            "student_fio": student.get("fio", ""),
            "room_id": room.get("id", ""),
        }


# Диалог создания заявки на выселение с выбором студента и комнаты
class VyselRequestDialog(QDialog):
    def __init__(self, student_model, room_model, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать заявку на выселение")
        self.student_model = student_model
        self.room_model = room_model
        layout = QFormLayout(self)
        self.student_combo = QComboBox(self)
        for i in range(student_model.rowCount()):
            student = student_model._students[i]
            display = f"{student.get('id')} - {student.get('fio')}"
            self.student_combo.addItem(display, student)
        self.room_combo = QComboBox(self)
        for room in room_model._rooms:
            display = f"{room.get('id')} - Этаж: {room.get('etazh')}, Мест: {room.get('kol_mest')}, Свободно: {room.get('svobodno')}"
            self.room_combo.addItem(display, room)
        layout.addRow("Студент:", self.student_combo)
        layout.addRow("Комната:", self.room_combo)
        button_layout = QHBoxLayout()
        ok_button = AnimatedButton("ОК")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

    def get_request_data(self):
        student = self.student_combo.currentData()
        room = self.room_combo.currentData()
        return {
            "id": "",
            "type": "Выселение",
            "status": "Создана",
            "student_fio": student.get("fio", ""),
            "room_id": room.get("id", ""),
        }


# Виджет для отображения списка студентов с выбором всей строки
class StudentsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        filter_label = QLabel("Фильтр по ФИО:")
        self.filter_line_edit = QLineEdit()
        self.filter_line_edit.setPlaceholderText("Введите текст для поиска")
        self.filter_line_edit.textChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_line_edit, 1)
        layout.addLayout(filter_layout)

        self.students_model = StudentsTableModel(
            [
                {
                    "id": "1",
                    "fio": "Иванов Иван Иванович",
                    "pol": "М",
                    "vozrast": 20,
                    "kurs": 2,
                    "fakultet": "Физический",
                },
                {
                    "id": "2",
                    "fio": "Петрова Мария Сергеевна",
                    "pol": "Ж",
                    "vozrast": 19,
                    "kurs": 1,
                    "fakultet": "Химический",
                },
            ]
        )
        self.proxy_model = StudentsProxyModel()
        self.proxy_model.setSourceModel(self.students_model)

        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()
        add_button = AnimatedButton("Добавить студента")
        add_button.clicked.connect(self.add_student)
        edit_button = AnimatedButton("Редактировать студента")
        edit_button.clicked.connect(self.edit_student)
        delete_button = AnimatedButton("Удалить студента")
        delete_button.clicked.connect(self.delete_student)
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)

    def on_filter_changed(self, text):
        self.proxy_model.setFilterText(text)
        logging.info("Применён фильтр: %s", text)

    def add_student(self):
        dialog = AddEditStudentDialog(self)
        if dialog.exec() == QDialog.Accepted:
            student = dialog.get_student_data()
            student["id"] = str(self.students_model.rowCount() + 1)
            self.students_model.add_student(student)
            QMessageBox.information(self, "Успех", "Студент успешно добавлен.")

    def edit_student(self):
        selection = self.table_view.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "Ошибка", "Выберите студента для редактирования.")
            return
        proxy_index = selection[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        row = source_index.row()
        student = self.students_model.get_student(row)
        dialog = AddEditStudentDialog(self, student)
        if dialog.exec() == QDialog.Accepted:
            updated_student = dialog.get_student_data()
            updated_student["id"] = student["id"]
            self.students_model.update_student(row, updated_student)
            QMessageBox.information(self, "Успех", "Данные студента обновлены.")

    def delete_student(self):
        selection = self.table_view.selectionModel().selectedRows()
        if not selection:
            QMessageBox.warning(self, "Ошибка", "Выберите студента для удаления.")
            return
        proxy_index = selection[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        row = source_index.row()
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить студента?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.students_model.remove_student(row)
            QMessageBox.information(self, "Успех", "Студент удалён.")


# Виджет для отображения списка комнат с выбором всей строки
class RoomsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableView()
        self.rooms_model = RoomsTableModel(
            [
                {"id": "101", "etazh": "1", "kol_mest": "4", "svobodno": "2"},
                {"id": "102", "etazh": "1", "kol_mest": "3", "svobodno": "0"},
            ]
        )
        self.table.setModel(self.rooms_model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table)


# Виджет для работы с заявками; получает ссылки на модели студентов и комнат
class RequestsWidget(QWidget):
    def __init__(self, student_model, room_model):
        super().__init__()
        self.student_model = student_model
        self.room_model = room_model
        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()
        add_zasel_button = AnimatedButton("Создать заявку на заселение")
        add_zasel_button.clicked.connect(self.create_zasel_request)
        add_vysel_button = AnimatedButton("Создать заявку на выселение")
        add_vysel_button.clicked.connect(self.create_vysel_request)
        button_layout.addWidget(add_zasel_button)
        button_layout.addWidget(add_vysel_button)
        layout.addLayout(button_layout)
        self.requests_table = QTableView()
        self.requests_model = RequestsTableModel([])
        self.requests_table.setModel(self.requests_model)
        self.requests_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.requests_table.setSelectionBehavior(QTableView.SelectRows)
        self.requests_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.requests_table)

    def create_zasel_request(self):
        dialog = ZaselRequestDialog(self.student_model, self.room_model, self)
        if dialog.exec() == QDialog.Accepted:
            request = dialog.get_request_data()
            request["id"] = str(self.requests_model.rowCount() + 1)
            self.requests_model.add_request(request)
            QMessageBox.information(self, "Заселение", "Заявка на заселение создана.")

    def create_vysel_request(self):
        dialog = VyselRequestDialog(self.student_model, self.room_model, self)
        if dialog.exec() == QDialog.Accepted:
            request = dialog.get_request_data()
            request["id"] = str(self.requests_model.rowCount() + 1)
            self.requests_model.add_request(request)
            QMessageBox.information(self, "Выселение", "Заявка на выселение создана.")


# Асинхронное задание для генерации отчёта с использованием QRunnable
class WorkerSignals(QObject):
    progress = Signal(int)
    finished = Signal(bool)
    error = Signal(str)


class ReportWorkerRunnable(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._is_cancelled = False

    def run(self):
        try:
            for i in range(1, 101):
                if self._is_cancelled:
                    self.signals.finished.emit(False)
                    return
                time.sleep(0.03)
                self.signals.progress.emit(i)
            self.signals.finished.emit(True)
            logging.info("Отчёт успешно сгенерирован.")
        except Exception as e:
            logging.error("Ошибка генерации отчёта: %s", e)
            self.signals.error.emit(str(e))
            self.signals.finished.emit(False)


# Виджет для отчётности с использованием QThreadPool и QRunnable
class ReportsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.export_button = AnimatedButton("Выгрузить отчёт")
        self.export_button.clicked.connect(self.export_report)
        layout.addWidget(self.export_button)
        self.progress_dialog = None

    def export_report(self):
        self.progress_dialog = QProgressDialog(
            "Генерация отчёта...", "Отмена", 0, 100, self
        )
        self.progress_dialog.setWindowTitle("Отчёт")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.worker = ReportWorkerRunnable()
        self.worker.signals.progress.connect(self.progress_dialog.setValue)
        self.worker.signals.finished.connect(self.report_finished)
        self.progress_dialog.canceled.connect(
            lambda: setattr(self.worker, "_is_cancelled", True)
        )
        QThreadPool.globalInstance().start(self.worker)

    def report_finished(self, success):
        if success:
            QMessageBox.information(
                self, "Отчёт", "Отчёт успешно сгенерирован и выгружен."
            )
        else:
            QMessageBox.warning(self, "Отчёт", "Ошибка при генерации отчёта.")


# Главное окно приложения с дополнительным меню для просмотра логов
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система управления общежитием")
        self.setMinimumSize(900, 700)
        self._create_tabs()
        self._create_menu()

    def _create_tabs(self):
        self.tabs = QTabWidget()
        self.students_tab = StudentsWidget()
        self.rooms_tab = RoomsWidget()
        # Передаём модели студентов и комнат в виджет заявок
        self.requests_tab = RequestsWidget(
            self.students_tab.students_model, self.rooms_tab.rooms_model
        )
        self.reports_tab = ReportsWidget()
        self.tabs.addTab(self.students_tab, "Студенты")
        self.tabs.addTab(self.rooms_tab, "Комнаты")
        self.tabs.addTab(self.requests_tab, "Заявки")
        self.tabs.addTab(self.reports_tab, "Отчётность")
        self.setCentralWidget(self.tabs)

    def _create_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Файл")
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        logs_action = QAction("Просмотр логов", self)
        logs_action.triggered.connect(self.show_logs)
        file_menu.addAction(logs_action)

        help_menu = menu_bar.addMenu("Справка")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_about(self):
        QMessageBox.information(
            self, "О программе", "Система управления общежитием.\nВерсия 1.0\n© 2025"
        )

    def show_logs(self):
        dlg = LogViewerDialog(self)
        dlg.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    sys.excepthook = exception_hook
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
