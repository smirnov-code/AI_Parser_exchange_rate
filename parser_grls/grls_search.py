import random
from grls_captcha import solve_captcha_llm


def try_search_and_captcha(page, search_query):
    """Открывает сайт, ищет препарат с человеческими паузами. Возвращает True, если успешно."""
    page.goto("https://grls.rosminzdrav.ru/Default.aspx")
    page.wait_for_timeout(2000)

    try:
        # Клик по радиокнопке
        page.locator("#ctl00_plate_rblGrlsSearchMode_1").click()
        page.wait_for_timeout(random.uniform(1000, 1500))  # Пауза > 1 сек

        # Ввод текста
        page.locator("#seekgrls").fill(search_query)
        page.wait_for_timeout(random.uniform(1000, 2000))  # Пауза > 1 сек

        # Клик по кнопке "Найти"
        page.get_by_role("button", name="Найти").first.click()

        # Ждем 3 секунды, чтобы сайт подумал и показал капчу
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"    ❌ Ошибка на этапе поиска: {e}")
        return False

    # 5 попыток пройти капчу
    for attempt in range(5):
        captcha_img = page.locator("img[src*='captcha'], #ctl00_ContentPlaceHolder1_imgCaptcha").first

        if captcha_img.is_visible():
            print(f"    🔒 Капча (попытка {attempt + 1}/5). Ждем полной загрузки...")
            page.wait_for_timeout(2000)  # Даем картинке прогрузиться

            captcha_img.screenshot(path="current_captcha.png")
            code = solve_captcha_llm("current_captcha.png")

            if code:
                print(f"    🤖 Нейросеть прочитала: {code}")

                # Ввод капчи
                page.locator("input#ctl00_ContentPlaceHolder1_txtCaptcha, input[name*='Captcha']").fill(code)

                # Пауза перед кликом ОК (> 1 сек)
                page.wait_for_timeout(random.uniform(1000, 2000))

                page.locator("input#ctl00_ContentPlaceHolder1_btnOK, input[value='Ok']").click()

                # Ждем 4 секунды после ввода
                page.wait_for_timeout(4000)

                if page.locator("#ctl00_plate_grts1_qa-result-table").is_visible():
                    print("    ✅ Капча пройдена!")
                    return True
                else:
                    print("    ⚠️ Таблицы нет. Капча не подошла. Пробуем еще...")
                    page.reload()
                    page.wait_for_timeout(3000)
            else:
                print("    ❌ Не удалось распознать код. Обновляем...")
                page.reload()
                page.wait_for_timeout(3000)
        else:
            if page.locator("#ctl00_plate_grts1_qa-result-table").is_visible():
                return True
            else:
                return False

    return False  # Все 5 попыток провалились