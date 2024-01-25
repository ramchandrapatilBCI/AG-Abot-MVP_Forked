import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

driver=None
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])

@pytest.fixture(params=["chrome"],scope="class")
def driver_init(request):
    if request.param == "chrome":
        web_driver = webdriver.Chrome(options)
    if request.param == "firefox":
        web_driver = webdriver.Firefox()
    # strABOTURL=readConfigIni('ABOT_URL')
    web_driver.get('https://abot-test-001.azurewebsites.net/login')
    page_state = web_driver.execute_script('return document.readyState;')
    web_driver.maximize_window()
    web_driver.implicitly_wait(15)
    login_button=web_driver.find_element(By.XPATH, f"//button")
    login_button.click()
    web_driver.implicitly_wait(15)
    web_driver.find_element(By.XPATH, "//input[@name='username']").send_keys("ramchandra.patil@blenheimchalcot.com")
    web_driver.find_element(By.NAME, "action").click()
    web_driver.find_element(By.XPATH, "//input[@name='password']").send_keys('@Test12345')
    web_driver.implicitly_wait(15)
    web_driver.find_element(By.NAME, "action").click()
    web_driver.implicitly_wait(10)
    # actions.move_to_element(email_password).perform()
    print(web_driver.title)
    assert web_driver.title=='Abot'
    request.cls.driver = web_driver
    yield
    web_driver.find_element(By.XPATH, "//div[contains(@class,'MuiAvatar')]").click()
    web_driver.find_element(By.XPATH, "(//ul[@role='menu']/li[@role='menuitem'])[2]").click()
    web_driver.quit()


class BasicTest:
    pass

class Test_URL(BasicTest):
        @pytest.mark.usefixtures("driver_init")
        def test_WigonLogo(self):
            input=self.driver.find_element(By.XPATH, f"//img[@alt='logo']")
            assert input, 'Wigon Counsil logo is missing'

        @pytest.mark.usefixtures("driver_init")
        def test_BOTAvailibility(self):
            input=self.driver.find_element(By.ID, f"chat-input")
            assert input, 'input to enter query does not exist.'

        @pytest.mark.usefixtures("driver_init")
        def test_ClearInstrcutionsOnBOTWelcomeScreen(self):
            input = self.driver.find_element(By.ID, f"welcome-screen")
            assert input, 'input to enter query does not exist.'
