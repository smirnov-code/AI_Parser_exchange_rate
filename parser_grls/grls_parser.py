import os
import time
from playwright.sync_api import sync_playwright
from llm_matcher import choose_best_match
from grls_search import try_search_and_captcha

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def parse_drug(drug_name, manufacturer, save_dir, row_num):
    print(f"    [Парсер] Ищем: {drug_name} | Производитель: {manufacturer}")
    search_query = drug_name.split()[0] if drug_name else ""
    if not search_query: return None

    # Внешний цикл: 2 попытки с перезапуском браузера
    for browser_attempt in range(2):
        print(f"    🌐 Запуск браузера (попытка {browser_attempt + 1}/2)...")
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROME_PATH, headless=False, slow_mo=100)
            page = browser.new_context(accept_downloads=True).new_page()

            if not try_search_and_captcha(page, search_query):
                print("    ⚠️ 5 попыток не удались. Перезапускаем браузер...")
                browser.close()
                time.sleep(10)
                continue  # Идем на следующий круг

            # Если капча пройдена, ищем строку в таблице
            try:
                table = page.locator("#ctl00_plate_grts1_qa-result-table")
                table.wait_for(state="visible", timeout=5000)
                rows = table.locator("tr").all()[1:]

                parsed_rows = [{"id": i, "name": r.locator("td").nth(1).inner_text().strip(),
                                "manuf": r.locator("td").nth(3).inner_text().strip()} for i, r in enumerate(rows) if
                               r.locator("td").count() > 3]

                if not parsed_rows:
                    browser.close()
                    return None

                best_id = choose_best_match(drug_name, manufacturer, parsed_rows)
                if best_id is None:
                    browser.close()
                    return None

                print(f"    🎯 Кликаем по строке №{best_id + 1}")
                rows[best_id].click()
                page.wait_for_timeout(3000)

                # Скачивание PDF
                safe_name = "".join([c for c in drug_name if c.isalpha() or c.isdigit() or c in ' ._-']).rstrip()
                save_filename = f"{row_num}_{safe_name}.pdf"
                save_path = os.path.join(save_dir, save_filename)

                with page.expect_download(timeout=15000) as download_info:
                    page.get_by_text("Показать инструкции", exact=False).first.click()

                download_info.value.save_as(save_path)
                print(f"    ✅ Скачано: {save_filename}")
                browser.close()
                return save_filename

            except Exception as e:
                print(f"    ❌ Ошибка парсинга таблицы: {e}")
                browser.close()
                return None

    print("    ❌ Не удалось пройти капчу после 2 перезапусков. Пропуск.")
    return None


def download_instruction(drug_name, manufacturer, save_dir, row_num):
    return parse_drug(drug_name, manufacturer, save_dir, row_num)