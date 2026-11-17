import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter


class ExcelWorker:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = None
        self.current_index = 0
        self.results = {}

    def load_data(self):
        print(f"Чтение файла: {self.file_path}")
        self.df = pd.read_excel(self.file_path)

        # Жесткая проверка колонок, чтобы данные не "поехали"
        required_cols = ['Код', 'Номенклатура', 'Основной производитель', 'отс/рх/бад']
        missing = [col for col in required_cols if col not in self.df.columns]

        if missing:
            print("\n⚠️ ВНИМАНИЕ! В вашем Excel-файле не совпадают названия колонок.")
            print(f"Отсутствуют: {missing}")
            print(f"В файле найдены: {self.df.columns.tolist()}")
            print("Пожалуйста, переименуйте колонки в Excel, чтобы они точно совпадали с ожидаемыми.")
            raise ValueError("Несовпадение названий колонок.")

        self.df['Ссылка на инструкцию'] = ""
        print(f"Загружено {len(self.df)} строк.")

    def get_next_drug(self):
        if self.current_index < len(self.df):
            row = self.df.iloc[self.current_index]
            idx = self.df.index[self.current_index]
            self.current_index += 1

            return idx, {
                'code': str(row['Код']),
                'name': str(row['Номенклатура']),
                'manufacturer': str(row['Основной производитель']),
                'type': str(row['отс/рх/бад']).strip().lower()
            }
        return None, None

    def add_result(self, orig_idx, filename):
        self.results[orig_idx] = filename if filename else ""

    def save_chunk(self, start_row, end_row, output_path):
        """Сохраняет часть таблицы и подгоняет ширину столбцов"""
        chunk_df = self.df.iloc[start_row:end_row].copy()

        for i in range(start_row, end_row):
            orig_idx = self.df.index[i]
            if orig_idx in self.results:
                chunk_df.at[orig_idx, 'Ссылка на инструкцию'] = self.results[orig_idx]

        chunk_df.to_excel(output_path, index=False)

        # --- Автоподбор ширины столбцов ---
        wb = load_workbook(output_path)
        ws = wb.active

        for col_idx, column in enumerate(chunk_df.columns, start=1):
            # Считаем длину заголовка и максимальную длину данных
            max_length = len(str(column))
            for value in chunk_df[column]:
                if value is not None:
                    max_length = max(max_length, len(str(value)))

            # Ширина = длина + запас, но не более 130
            adjusted_width = min(max_length + 2, 60)

            # Устанавливаем ширину
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = adjusted_width

        wb.save(output_path)
        print(f"💾 Сохранен файл (с автоподбором ширины): {output_path}")