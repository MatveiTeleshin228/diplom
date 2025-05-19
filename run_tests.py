import unittest
import os
import sys

def run_tests():
    # Получаем абсолютный путь к корню проекта
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Добавляем корень в PYTHONPATH
    sys.path.insert(0, project_root)
    
    # Проверяем существование папки tests
    tests_dir = os.path.join(project_root, 'tests')
    if not os.path.exists(tests_dir):
        raise FileNotFoundError(f"Tests directory not found: {tests_dir}")
    
    # Проверяем наличие __init__.py
    init_file = os.path.join(tests_dir, '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# Package initialization')
    
    # Настройка тестов
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=tests_dir,
        pattern='test_*.py',
        top_level_dir=project_root
    )
    
    # Запуск тестов
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        sys.exit(1)