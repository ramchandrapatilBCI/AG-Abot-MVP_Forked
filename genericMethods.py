from selenium.webdriver.common.by import By
from configparser import ConfigParser
from selenium.common.exceptions import NoSuchElementException


def readConfigIni(Key):
    config = ConfigParser()
    config.read('../config.ini')
    print(config.sections())
    return config.get(Key)


def matchString(str, text_list):
    flag = False
    for s in text_list:
        if str in s:
            flag = True
            break
    return flag


def check_exists_by_ID(driver, locator):
    try:
        driver.find_element(By.ID, locator)
    except NoSuchElementException:
        return False
    return True
