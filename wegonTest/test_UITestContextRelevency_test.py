import pytest
from deepeval import evaluate
from deepeval.metrics import ContextualRelevancyMetric
from deepeval.test_case import LLMTestCase
from selenium import webdriver
from genericMethods import matchString
from genericMethods import readConfigIni
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from genericMethods import matchString
from genericMethods import readConfigIni
from time import sleep
from selenium.webdriver.common.action_chains import ActionChains


driver=None
options = webdriver.ChromeOptions()

@pytest.fixture(params=["chrome"])
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
    assert web_driver.title=='Abot'
    request.cls.driver = web_driver
    # yield
    # web_driver.find_element(By.XPATH, "//div[contains(@class,'MuiAvatar')]").click()
    # web_driver.find_element(By.XPATH, "(//ul[@role='menu']/li[@role='menuitem'])[2]").click()
    # web_driver.quit()
    
@pytest.fixture
def metric():
    return ContextualRelevancyMetric(
        minimum_score=0.1,
        model="gpt-4-1106-preview",
        include_reason=True
    )

class BasicTest:
    pass

class Test_URL(BasicTest):
    @pytest.mark.usefixtures("driver_init")
    def test_WigonLogin(self):
        print(self.driver.title)
        assert self.driver.title=='Abot'

    @pytest.mark.usefixtures("driver_init")
    def test_contextual_Hi(self):
        input=self.driver.find_element(By.ID, f"chat-input")
        input.send_keys('Hi, I am looking for help')
        input.send_keys(Keys.ENTER)
        self.driver.implicitly_wait(15)
        label=self.driver.find_elements(By.XPATH,"(//div[@class='markdown-body']//p)[2]")
        test_case = LLMTestCase(
            input='Hi, I am looking for help',
            actual_output=label[0].text,
            retrieval_context=["Hello! May I know your name, please?",
                            "If you have any questions or need assistance with social care, I'm here to help. Please let me know how I can support you by providing more details about your situation. If you need to end this chat, you can type \"end\" at any time."]
        )

        metric = ContextualRelevancyMetric()  # Replace with the actual class for your metric
        metric.measure(test_case)        
        assert metric.score >= 0.5

    @pytest.mark.usefixtures("driver_init")
    def test_contextual_Help(self):
        input=self.driver.find_element(By.ID, f"chat-input")
        input.send_keys('Hi, I need your help')
        input.send_keys(Keys.ENTER)
        self.driver.implicitly_wait(15)
        label=self.driver.find_elements(By.XPATH,"(//div[@class='markdown-body']//p)[2]")
        test_case = LLMTestCase(
            input='Hi, I need your help',
            actual_output=label[0].text,
            retrieval_context=["Hello! May I know your name, please?",
                            "If you have any questions or need assistance with social care, I'm here to help. Please let me know how I can support you by providing more details about your situation. If you need to end this chat, you can type \"end\" at any time."]
        )
        metric = ContextualRelevancyMetric()  # Replace with the actual class for your metric
        metric.measure(test_case)
        assert metric.score >= 0.5

    @pytest.mark.usefixtures("driver_init")
    def test_RandomQueryAndResponse(self):
        input=self.driver.find_element(By.ID, f"chat-input")
        input.send_keys("Hi, I need your help")
        input.send_keys(Keys.ENTER)
        self.driver.implicitly_wait(15)
        input.send_keys("jfhksdhkfsd jkhdskjhfdskh dsjdsjkhkh")
        input.send_keys(Keys.ENTER)
        label=self.driver.find_elements(By.XPATH,"(//div[@class='markdown-body']//p)[4]")
        test_case = LLMTestCase(
        input='Hi, I need your help',
        actual_output=label[0].text,
        retrieval_context=["It seems there might have been a typing error. How can I help you with social care support today? If you have any issues or concerns, please let me know so I can assist you accordingly.","Hello! It seems there might be a typo in your message. How can I assist you with social care support today?"]
    )
        metric = ContextualRelevancyMetric()  # Replace with the actual class for your metric
        metric.measure(test_case)
        assert metric.score >= 0.5

    @pytest.mark.usefixtures("driver_init")
    def test_QueryTOBot(self):
        input = self.driver.find_element(By.ID, f"chat-input")
        input.send_keys("Hi, I need your help")
        input.send_keys(Keys.ENTER)
        self.driver.implicitly_wait(15)
        input.send_keys("jfhksdhkfsd jkhdskjhfdskh dsjdsjkhkh")
        input.send_keys(Keys.ENTER)
        label = self.driver.find_elements(By.XPATH, "(//div[@class='markdown-body']//p)[4]")
        test_case = LLMTestCase(
            input='Hi, I need your help',
            actual_output=label[0].text,
            retrieval_context=[
                "It seems there might have been a typing error. How can I help you with social care support today? If you have any issues or concerns, please let me know so I can assist you accordingly.",
                "Hello! It seems there might be a typo in your message. How can I assist you with social care support today?"]
        )
        metric = ContextualRelevancyMetric()  # Replace with the actual class for your metric
        metric.measure(test_case)
        assert metric.score >= 0.5

    @pytest.mark.usefixtures("driver_init")
    def test_AnswerFromBot(self):
        input = self.driver.find_element(By.ID, f"chat-input")
        input.send_keys("Hi, I need your help")
        input.send_keys(Keys.ENTER)
        self.driver.implicitly_wait(15)
        input.send_keys("jfhksdhkfsd jkhdskjhfdskh dsjdsjkhkh")
        input.send_keys(Keys.ENTER)
        label = self.driver.find_elements(By.XPATH, "(//div[@class='markdown-body']//p)[4]")
        test_case = LLMTestCase(
            input='Hi, I need your help',
            actual_output=label[0].text,
            retrieval_context=[
                "It seems there might have been a typing error. How can I help you with social care support today? If you have any issues or concerns, please let me know so I can assist you accordingly.",
                "Hello! It seems there might be a typo in your message. How can I assist you with social care support today?"]
        )
        metric = ContextualRelevancyMetric()  # Replace with the actual class for your metric
        metric.measure(test_case)
        assert metric.score >= 0.5

    @pytest.mark.usefixtures("driver_init")
    def test_OtherQueriesToBOT(self):
        input = self.driver.find_element(By.ID, f"chat-input")
        input.send_keys("Hi, I need your help")
        input.send_keys(Keys.ENTER)
        self.driver.implicitly_wait(15)
        input.send_keys("jfhksdhkfsd jkhdskjhfdskh dsjdsjkhkh")
        input.send_keys(Keys.ENTER)
        label = self.driver.find_elements(By.XPATH, "(//div[@class='markdown-body']//p)[4]")
        test_case = LLMTestCase(
            input='Hi, I need your help',
            actual_output=label[0].text,
            retrieval_context=[
                "It seems there might have been a typing error. How can I help you with social care support today? If you have any issues or concerns, please let me know so I can assist you accordingly.",
                "Hello! It seems there might be a typo in your message. How can I assist you with social care support today?"]
        )
        metric = ContextualRelevancyMetric()  # Replace with the actual class for your metric
        metric.measure(test_case)
        assert metric.score >= 0.5

    @pytest.mark.usefixtures("driver_init")
    def test_RememberenceOfTheContext(self):
        input = self.driver.find_element(By.ID, f"chat-input")
        input.send_keys("Hi, I need your help")
        input.send_keys(Keys.ENTER)
        self.driver.implicitly_wait(15)
        input.send_keys("jfhksdhkfsd jkhdskjhfdskh dsjdsjkhkh")
        input.send_keys(Keys.ENTER)
        label = self.driver.find_elements(By.XPATH, "(//div[@class='markdown-body']//p)[4]")
        test_case = LLMTestCase(
            input='Hi, I need your help',
            actual_output=label[0].text,
            retrieval_context=[
                "It seems there might have been a typing error. How can I help you with social care support today? If you have any issues or concerns, please let me know so I can assist you accordingly.",
                "Hello! It seems there might be a typo in your message. How can I assist you with social care support today?"]
        )
        metric = ContextualRelevancyMetric()  # Replace with the actual class for your metric
        metric.measure(test_case)
        assert metric.score >= 0.5
        
