import sys
import socket
from PySide6.QtWidgets import QApplication, QMessageBox

def is_internet_available():
    """Проверяет интернет без зависимостей от БД"""
    try:
        # Проверяем доступность DNS Google (быстрее чем HTTP запрос)
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def main():
    # 1. Проверка интернета ДО всего остального
    if not is_internet_available():
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "Нет подключения",
            "Отсутствует интернет-соединение.\n"
            "Приложение не может работать без интернета.",
            QMessageBox.Ok
        )
        sys.exit(1)  # Выходим сразу
    
    # 2. Только если интернет есть - импортируем и запускаем основное приложение
    from dip import MainWindow
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()