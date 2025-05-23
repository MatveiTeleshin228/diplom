import pytest
from PySide6.QtWidgets import QApplication
import sys

@pytest.fixture(scope="session")
def qapp():
    """Фикстура для QApplication с обработкой исключений"""
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
    # Корректное закрытие
    for widget in app.allWidgets():
        widget.close()
    app.quit()