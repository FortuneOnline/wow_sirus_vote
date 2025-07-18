from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import MoveTargetOutOfBoundsException
import time
import undetected_chromedriver as uc
import os
import json
from selenium.webdriver.chrome.options import Options


def load_config():
    config_path = "config.txt"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            lines = f.readlines()
            if len(lines) >= 3:
                return {
                    "username": lines[0].strip(),
                    "password": lines[1].strip(),
                    "nickname": lines[2].strip()
                }
    return None


def save_config(username, password, nickname):
    with open("config.txt", "w") as f:
        f.write(f"{username}\n{password}\n{nickname}\n")


def save_cookies(driver):
    cookies = driver.get_cookies()
    with open('cookies.json', 'w') as f:
        json.dump(cookies, f)


def load_cookies(driver):
    if os.path.exists('cookies.json'):
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        return True
    return False


def get_user_input():
    config = load_config()

    if config:
        print("Найдены сохраненные данные:")
        print(f"Логин: {config['username']}")
        print(f"Пароль: {'*' * len(config['password'])}")
        print(f"Никнейм: {config['nickname']}")
        return config

    print("Пожалуйста, введите данные для голосования:")
    username = input("Email/Логин: ")
    password = input("Пароль: ")
    nickname = input("Никнейм для голосования: ")

    save_config(username, password, nickname)

    return {
        "username": username,
        "password": password,
        "nickname": nickname
    }


def scroll_humanlike(driver, scroll_pause_time=0.5):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def main():
    user_data = get_user_input()
    USERNAME = user_data["username"]
    PASSWORD = user_data["password"]
    NICKNAME = user_data["nickname"]
    URL = "https://wow.mmotop.ru/servers/5130/votes/new"

    # Настройка опций Chrome для сохранения сессии
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")

    try:
        driver = uc.Chrome(options=options)
        driver.get(URL)

        # Пробуем загрузить куки перед проверкой авторизации
        cookies_loaded = load_cookies(driver)
        if cookies_loaded:
            print("Куки загружены, проверяем авторизацию...")
            driver.refresh()  # Обновляем страницу после загрузки куки

        # Проверяем авторизацию
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.fleft.nickname"))
            )
            nickname_element = driver.find_element(By.CSS_SELECTOR, "div.fleft.nickname")
            print(f"Уже авторизованы как: {nickname_element.text.strip()}")
        except:
            print("Выполняем авторизацию...")
            auth_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.btn.btn-small.fright.enter"))
            )
            auth_button.click()

            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "user_email"))
            )
            password_field = driver.find_element(By.ID, "user_password")
            submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Войти']")

            email_field.send_keys(USERNAME)
            password_field.send_keys(PASSWORD)
            time.sleep(1)
            scroll_humanlike(driver)
            submit_button.click()

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.fleft.nickname"))
                )
                print("Авторизация прошла успешно!")
                # Сохраняем куки после успешной авторизации
                save_cookies(driver)
                print("Куки сохранены для будущих сессий")
            except:
                print("Ошибка авторизации. Проверьте логин и пароль.")
                driver.quit()
                return

            # Возвращаемся на страницу голосования
            driver.get(URL)

        # Основной процесс голосования
        slider = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "Slider"))
        )

        print("Сдвигаем слайдер...")
        slider_width = slider.size['width']
        actions = ActionChains(driver)
        actions.click_and_hold(slider).perform()

        for i in range(1, 101, 10):
            try:
                x_offset = i * slider_width / 100
                actions.move_by_offset(x_offset, 0).perform()
                time.sleep(0.01)
            except MoveTargetOutOfBoundsException:
                print(f"Превышение границ при перемещении на {x_offset}px, продолжаем...")
                continue

        time.sleep(0.5)
        actions.release().perform()
        time.sleep(1)
        scroll_humanlike(driver)

        nickname_field = driver.find_element(By.ID, "vote_4br3pv")
        nickname_field.clear()
        nickname_field.send_keys(NICKNAME)
        time.sleep(1)

        vote_button = driver.find_element(By.ID, "check_vote_form")
        vote_button.click()
        print("Голосование завершено!")
        time.sleep(5)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()