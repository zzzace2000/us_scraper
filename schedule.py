import os.path
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options


wait_timeout = 80
refresh_interval = 30


def reschedule(email, password, place, required_date):
    # Login
    options = Options()
    options.headless = True

    c_service = FirefoxService(executable_path=GeckoDriverManager().install())
    driver = webdriver.Firefox(service=c_service, options=options)

    try:
        result = _reschedule(email, password, place, required_date, driver)
    finally:
        if driver:
            driver.quit()
        if c_service:
            c_service.stop()
    return result


def _reschedule(email, password, place, required_date, driver):
    # Login
    # driver.get("https://ais.usvisa-info.com/%s/niv/users/sign_in" % country_code)
    driver.get("https://ais.usvisa-info.com/en-ca/niv/schedule/41520489/appointment")

    def wait_loading(xpath, by=By.XPATH, option="locate"):
        try:
            if option == "locate":
                element_present = EC.presence_of_element_located((by, xpath))
            elif option == "clickable":
                element_present = EC.element_to_be_clickable((by, xpath))
            WebDriverWait(driver, wait_timeout).until(element_present)
        except TimeoutException:
            print("Timed out waiting for page to load")
            driver.execute_script("window.scrollTo(0, 1080)")
            driver.save_screenshot("test.png")

    # Click OK to remove the dialog box
    ok_button_xpath = "//button[contains(text(), 'OK')]"
    wait_loading(ok_button_xpath)
    ok_button = driver.find_element(By.XPATH, ok_button_xpath)
    ok_button.click()

    # Then login
    email_box = driver.find_element(By.ID, "user_email")
    email_box.clear()
    email_box.send_keys(email)
    password_box = driver.find_element(By.ID, "user_password")
    password_box.clear()
    password_box.send_keys(password)
    driver.execute_script("document.getElementById('policy_confirmed').click()")
    signin_button = driver.find_element(By.NAME, "commit")
    signin_button.click()

    # Choose Continue for all applicants
    continue_button_xpath = "//input[@value='Continue']"
    wait_loading(continue_button_xpath, option="clickable")
    continue_button = driver.find_element(By.XPATH, continue_button_xpath)
    continue_button.click()

    # Choose select
    title_xpath = "//p[contains(text(), 'Please select the Consular Section location')]"
    wait_loading(title_xpath)

    # Choose the place
    select = Select(driver.find_element(By.ID, 'appointments_consulate_appointment_facility_id'))
    select.select_by_visible_text(place)

    time.sleep(3)

    # Choose the date:
    # First, click the date calendar.
    # Since now it's July, the left would be July, and the right would be August.
    # So my wanted date would be within this panel, so no need to click next to switch to next
    # month. So just find the first available date
    date_input = driver.find_element(By.ID, "appointments_consulate_appointment_date")
    date_input.click()
    time.sleep(3)

    # Choose the date
    date_panel = driver.find_element(By.ID, "ui-datepicker-div")
    while True:
        try:
            date_panel.find_element(By.TAG_NAME, 'div')
            break
        except NoSuchElementException:
            time.sleep(0.1)

    ## (TOREMOVE) Click the right for 7 times to move to Feb to test
    # for _ in range(6):
    #     right_panel = date_panel.find_element(By.CLASS_NAME, "ui-datepicker-group-last")
    #     next_btn = right_panel.find_element(By.TAG_NAME, 'a')
    #     next_btn.click()
    #     print('Click Next')
    #     time.sleep(1)
    left_panel = date_panel.find_element(By.CLASS_NAME, "ui-datepicker-group-first")
    left_table = left_panel.find_element(By.TAG_NAME, "table")
    try:
        avai_date = left_table.find_element(By.TAG_NAME, "a") # <a>
    except NoSuchElementException:
        right_panel = date_panel.find_element(By.CLASS_NAME, "ui-datepicker-group-last")
        right_table = right_panel.find_element(By.TAG_NAME, "table")

        try:
            avai_date = right_table.find_element(By.TAG_NAME, "a") # <a>
        except NoSuchElementException:
            print('No date found in both left and right panels. Quit!')
            return None

    avai_date.click()
    time.sleep(3)

    # Wait for the time of appointment shows up
    time_select = driver.find_element(By.ID, 'appointments_consulate_appointment_time')
    while len(time_select.find_elements(By.TAG_NAME, 'option')) == 1:
        time.sleep(0.1)

    # Then first check the date selected is indeed the date requested
    date_selected = date_input.get_attribute('value')
    if date_selected > required_date:
        print(f'The date selected {date_selected} is later than the date {required_date}. Quit.')
        return None

    select = Select(time_select)
    select.select_by_index(index=len(select.options)-1) # First available

    attempts = 0
    while attempts < 5:
        wait_loading('appointments_submit', By.ID, option='clickable')
        submit_btn = driver.find_element(By.ID, "appointments_submit")
        submit_btn.click()

        time.sleep(3)

        confirm_button_xpath = "//a[contains(text(), 'Confirm')]"
        wait_loading(confirm_button_xpath, option='clickable')
        confirm_btn = driver.find_element(By.XPATH, confirm_button_xpath)
        confirm_btn.click()

        time.sleep(3)

        get_source = driver.page_source
        if '429 Too Many' not in get_source:
            break

        driver.save_screenshot(f"fail_attempt_{place}_{required_date}_{attempts}.png")
        driver.execute_script("window.history.go(-1)")

        attempts += 1
        print('Attempt %d' % attempts)
        time.sleep(3)


    if attempts >= 5:
        print('Tried 5 times of refresh but not succeed.')
        return None

    idx = 0
    while os.path.exists(f"success_rebook_{idx}.png"):
        idx += 1
    driver.save_screenshot(f"success_rebook_{idx}.png")
    return date_selected


if __name__ == '__main__':
    result = reschedule(
        email='zzzace2000@gmail.com',
        password='',
        place='Toronto',
        required_date='2022-08-01',
    )

    if result:
        print('Success!')
    else:
        print('Fail to schedule')
