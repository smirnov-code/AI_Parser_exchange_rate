import os
import time
import random
from excel_worker import ExcelWorker
from grls_parser import download_instruction
# Импортируем функцию очистки из нашего мини-скрипта
from clear_folders import clear_directory

# --- НАСТРОЙКИ ---
INPUT_FILE = "test_sample.xlsx"
OUTPUT_DIR = "results"
DOWNLOAD_DIR = "downloads"
CHUNK_SIZE = 20

# Настройки "ночного" режима
MIN_DELAY = 70
MAX_DELAY = 90


def get_chunk_folder(start_num, end_num):
    folder_name = f"{start_num} - {end_num}"
    path = os.path.join(DOWNLOAD_DIR, folder_name)
    os.makedirs(path, exist_ok=True)
    return path


def main():
    # --- ОЧИСТКА ПАПОК ПЕРЕД ЗАПУСКОМ ---
    print("🧹 Очистка старых результатов...")
    clear_directory(DOWNLOAD_DIR)
    clear_directory(OUTPUT_DIR)

    # Инициализируем работу с Excel
    excel = ExcelWorker(INPUT_FILE)
    try:
        excel.load_data()
    except Exception as e:
        print(f"Ошибка загрузки Excel: {e}")
        return

    total_rows = len(excel.df)
    print(f"🚀 Всего строк: {total_rows}. Разбиваем на пачки по {CHUNK_SIZE}.")

    # Счетчики для статистики
    total_processed = 0
    total_downloaded = 0
    total_bad = 0
    total_not_found = 0

    # Идем по таблице шагами по 20
    for start_idx in range(0, total_rows, CHUNK_SIZE):
        end_idx = min(start_idx + CHUNK_SIZE, total_rows)

        start_num = start_idx + 1
        end_num = end_idx

        print(f"\n📦 НАЧАЛО ПАЧКИ: {start_num} - {end_num}")

        pdf_folder = get_chunk_folder(start_num, end_num)
        result_folder = os.path.join(OUTPUT_DIR, f"{start_num} - {end_num}")
        os.makedirs(result_folder, exist_ok=True)

        for i in range(start_idx, end_idx):
            orig_idx, drug_data = excel.get_next_drug()
            if drug_data is None: break

            row_num = start_num + (i - start_idx)
            total_processed += 1
            print(f"  [{row_num}] {drug_data['name']}")

        if 'бад' in drug_data['type']:
            print("  ⏭️ БАД. Пропуск.")
            filename = ""
            total_bad += 1
            # Паузы нет, идем дальше
        else:
            print(f"  🔍 Ищем на ГРЛС (Производитель: {drug_data['manufacturer']})...")

            # Вызов парсера
            filename = download_instruction(
                drug_name=drug_data['name'],
                manufacturer=drug_data['manufacturer'],
                save_dir=pdf_folder,
                row_num=row_num
            )

            if filename:
                # Формируем путь для гиперссылки
                filename = os.path.join(pdf_folder, filename)
                total_downloaded += 1
            else:
                total_not_found += 1

            # Пауза теперь ТОЛЬКО здесь (после реального поиска, кроме последнего препарата)
            if total_processed < total_rows:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"  ⏳ Пауза {delay:.1f} сек...")
                time.sleep(delay)

        excel.add_result(orig_idx, filename)

        # Когда пачка из 20 штук закончилась — сохраняем её
        result_file_path = os.path.join(result_folder, f"Result_{start_num} - {end_num}.xlsx")
        excel.save_chunk(start_idx, end_idx, result_file_path)

    print("\n🎉 Все пачки обработаны!")
    print("\n📊 ИТОГИ:")
    print(f"Всего обработано: {total_processed}")
    print(f"БАДы (пропущены): {total_bad}")
    print(f"Инструкции скачаны: {total_downloaded}")
    print(f"Не найдены/Ошибки: {total_not_found}")


if __name__ == "__main__":
    main()
