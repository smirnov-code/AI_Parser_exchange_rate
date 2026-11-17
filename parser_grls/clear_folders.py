import os
import shutil

# Настройки путей (должны совпадать с main.py)
DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "results"

def clear_directory(folder_path):
    """Удаляет всё содержимое папки, но оставляет саму папку"""
    if not os.path.exists(folder_path):
        print(f"Папка '{folder_path}' не найдена, пропускаем.")
        return

    print(f"Очистка папки: {folder_path}...")
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"  ❌ Не удалось удалить {file_path}. Причина: {e}")
    print(f"  ✅ Папка '{folder_path}' очищена.")

if __name__ == "__main__":
    print("--- Запуск очистки папок ---")
    clear_directory(DOWNLOAD_DIR)
    clear_directory(OUTPUT_DIR)
    print("--- Готово! Можно запускать парсер заново. ---")