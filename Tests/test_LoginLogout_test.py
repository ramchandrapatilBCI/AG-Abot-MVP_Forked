import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from genericMethods import check_exists_by_ID


class TestLogin:

    @pytest.fixture
    def driver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument('headless')
        options.add_argument("--disable-dev-shm-usage")
        prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
        options.add_experimental_option("prefs", prefs)
        web_driver = webdriver.Chrome(options=options)
        web_driver.get('https://abot-test-001.azurewebsites.net/login')
        web_driver.execute_script('return document.readyState;')
        web_driver.maximize_window()
        web_driver.implicitly_wait(15)
        yield web_driver
        web_driver.quit()
        web_driver.stop_client()

    @pytest.fixture
    def driver1(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
        options.add_experimental_option("prefs", prefs)
        web_driver = webdriver.Chrome(options=options)
        web_driver.get('https://abot-test-001.azurewebsites.net/login')
        web_driver.execute_script('return document.readyState;')
        web_driver.maximize_window()
        web_driver.implicitly_wait(15)
        yield web_driver
        web_driver.quit()

    @pytest.mark.usefixtures("driver")
    def test_LoginSuccessful(self, driver):
        login_button = driver.find_element(By.XPATH, "//div[@class='MuiStack-root css-eb1amy']")
        login_button.click()
        driver.implicitly_wait(15)
        driver.find_element(By.XPATH, "//input[@name='username']").send_keys("ramchandra.patil@blenheimchalcot.com")
        driver.find_element(By.NAME, "action").click()
        driver.find_element(By.XPATH, "//input[@name='password']").send_keys('@Test12345')
        driver.find_element(By.NAME, "action").click()
        driver.implicitly_wait(10)
        print("printing Title->", driver.title)
        assert driver.title == 'Log in | Cura'

    @pytest.mark.usefixtures("driver")
    def test_LoginUnSuccessful_InvalidPassword(self, driver):
        login_button=driver.find_element(By.XPATH, f"//div[@class='MuiStack-root css-eb1amy']")
        login_button.click()
        driver.implicitly_wait(15)
        driver.find_element(By.XPATH, "//input[@name='username']").send_keys("ramchandra.patil@blenheimchalcot.com")
        driver.find_element(By.NAME, "action").click()
        driver.find_element(By.XPATH, "//input[@name='password']").send_keys('@Test123456')
        driver.find_element(By.NAME, "action").click()
        driver.implicitly_wait(15)
        assert check_exists_by_ID(driver, "error-element-password")

    @pytest.mark.usefixtures("driver")
    def test_LoginUnSuccessful_InvalidCredCombinationPassword(self, driver):
        login_button=driver.find_element(By.XPATH, f"//button")
        login_button.click()
        driver.implicitly_wait(15)
        driver.find_element(By.XPATH, "//input[@name='username']").send_keys("ramchandra.patil@blenheimchalcot.com")
        driver.find_element(By.NAME, "action").click()
        driver.find_element(By.NAME, "action").click()
        driver.find_element(By.XPATH, "//input[@name='password']").send_keys('@Test1234523')
        driver.implicitly_wait(15)
        driver.find_element(By.NAME, "action").click()
        driver.implicitly_wait(15)
        assert check_exists_by_ID(driver, "error-element-password")

    @pytest.mark.usefixtures("driver")
    def test_LogoutABOT(self, driver):
        login_button = driver.find_element(By.XPATH, "//div[@class='MuiStack-root css-eb1amy']")
        login_button.click()
        driver.implicitly_wait(15)
        driver.find_element(By.XPATH, "//input[@name='username']").send_keys("testing@cura.com")
        driver.find_element(By.NAME, "action").click()
        driver.find_element(By.XPATH, "//input[@name='password']").send_keys('eV030UqN')
        driver.find_element(By.NAME, "action").click()
        driver.implicitly_wait(10)
        print("printing Title->", driver.title)
        assert driver.title == 'Cura'
        driver.find_element(By.XPATH, "//img[contains(@class,'MuiAvatar')]").click()
        time.sleep(5)
        driver.find_element(By.XPATH, "//li[contains(.,'Logout')]").click()
        print("printing Title->", driver.title)
        assert driver.title == 'Cura'

    @pytest.mark.usefixtures("driver", "driver1")
    def test_SessionTimeOut(self, driver, driver1):
        driver_anotherInstance=driver1
        login_button = driver.find_element(By.XPATH, "//div[@class='MuiStack-root css-eb1amy']")
        login_button.click()
        driver.implicitly_wait(15)
        driver.find_element(By.XPATH, "//input[@name='username']").send_keys("testing@cura.com")
        driver.find_element(By.NAME, "action").click()
        driver.find_element(By.XPATH, "//input[@name='password']").send_keys('eV030UqN')
        driver.find_element(By.NAME, "action").click()
        driver.implicitly_wait(10)
        print("printing Title->", driver.title)
        assert driver.title == 'Cura'
        driver_anotherInstance.get('https://abot-test-001.azurewebsites.net/login')
        driver_anotherInstance.implicitly_wait(15)
        login_button = driver_anotherInstance.find_element(By.XPATH, "//div[@class='MuiStack-root css-eb1amy']")
        login_button.click()
        driver_anotherInstance.implicitly_wait(15)
        driver_anotherInstance.find_element(By.XPATH, "//input[@name='username']").send_keys("testing@cura.com")
        driver_anotherInstance.find_element(By.NAME, "action").click()
        driver_anotherInstance.find_element(By.XPATH, "//input[@name='password']").send_keys('eV030UqN')
        driver_anotherInstance.find_element(By.NAME, "action").click()
        driver_anotherInstance.implicitly_wait(10)
        print("printing Title->", driver_anotherInstance.title)
        assert driver_anotherInstance.title == 'Cura'

        driver_anotherInstance.find_element(By.XPATH, "//img[contains(@class,'MuiAvatar')]").click()
        time.sleep(5)
        driver_anotherInstance.find_element(By.XPATH, "//li[contains(.,'Logout')]").click()
        print("printing Title->", driver.title)
        assert driver.title == 'Cura'
        time.sleep(6)
        assert driver_anotherInstance.title == 'Cura'
