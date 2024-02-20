import time
from telnetlib3 import EC
# from selenium.webdriver.support import expected_conditions as EC
import pytest
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


class TestUITest:

    @pytest.fixture
    def driver(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument('headless')
        prefs = {"credentials_enable_service": False, "profile.password_manager_enabled": False}
        options.add_experimental_option("prefs", prefs)
        web_driver = webdriver.Chrome(options)
        web_driver.get('https://abot-test-001.azurewebsites.net/login/')
        web_driver.execute_script('return document.readyState;')
        web_driver.maximize_window()
        web_driver.implicitly_wait(15)
        login_button = web_driver.find_element(By.XPATH, "//div[@class='MuiStack-root css-eb1amy']")
        login_button.click()
        web_driver.implicitly_wait(15)
        web_driver.find_element(By.XPATH, "//input[@name='username']").send_keys("testing@cura.com")
        web_driver.find_element(By.NAME, "action").click()
        web_driver.find_element(By.XPATH, "//input[@name='password']").send_keys('eV030UqN')
        web_driver.find_element(By.NAME, "action").click()
        web_driver.implicitly_wait(10)
        print("printing Title->", web_driver.title)
        assert web_driver.title == 'Cura'
        yield web_driver
        web_driver.quit()

    @pytest.mark.usefixtures("driver")
    def test_LogoTest(self, driver):
        ele_input = driver.find_element(By.XPATH, f"//img[@alt='logo']")
        assert ele_input, 'Wigon Counsil logo is missing'

    # @pytest.mark.usefixtures("driver")
    # def test_Transcript(self, driver):
    #     time.sleep(5)
    #     chat_input = driver.find_element(By.ID, f"chat-input")
    #     ActionChains(driver).move_to_element(chat_input).click(chat_input).perform()
    #     chat_input.send_keys(Keys.ENTER)
    #     driver.implicitly_wait(15)
    #     chat_input.send_keys("jfhksdhkfsd jkhdskjhfdskh dsjdsjkhkh")
    #     chat_input.send_keys(Keys.ENTER)
    #     driver.find_element(By.XPATH, "//div[@id='actions-list']").click()
    #     ele_input = driver.find_element(By.XPATH, f"//code")
    #     assert ele_input, 'Transcript is NOT generated'
    #
    # @pytest.mark.usefixtures("driver")
    # def test_NewChatPopupWindow(self, driver):
    #     driver.implicitly_wait(15)
    #     driver.find_element(By.ID, f"new-chat-button").click()
    #     driver.implicitly_wait(15)
    #     popup = driver.find_element(By.ID, "new-chat-dialog")
    #     assert popup.is_displayed(), 'Popup is NOT displayed'
    #
    # @pytest.mark.usefixtures("driver")
    # def test_NewChatPopupWindowConfirm(self, driver):
    #     flag = True
    #     try:
    #         driver.implicitly_wait(15)
    #         driver.find_element(By.ID, f"new-chat-button").click()
    #         driver.implicitly_wait(15)
    #         popup = driver.find_element(By.ID, "new-chat-dialog")
    #         assert popup, 'Popup is NOT displayed'
    #         driver.find_element(By.ID, "confirm").click()
    #         popup = driver.find_element(By.ID, "new-chat-dialog")
    #         if (popup.is_displayed()):
    #             flag = False
    #         assert flag, 'Popup is displayed'
    #     except:
    #         print("Exception occured")
    #
    # @pytest.mark.usefixtures("driver")
    # def test_ThumbUPDownExistence(self, driver):
    #     try:
    #         # Find the chat input field by ID and send a message
    #         chat_input = driver.find_element(By.ID, "chat-input")
    #         chat_input.send_keys("Hi, I need your help")
    #         chat_input.send_keys(Keys.ENTER)
    #
    #         # Wait for elements to load (adjust the time as needed)
    #         driver.implicitly_wait(15)
    #
    #         # Find the thumbs-up icon by XPath
    #         thumbs_up_icon = driver.find_element(By.XPATH, "//span[@aria-label='Helpful']")
    #
    #         # Check if the thumbs-up icon is displayed
    #         assert not thumbs_up_icon.is_displayed(), 'ThumbsUP not DISPLAYED'
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {str(e)}")
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_ThumbDownExistence(self, driver):
    #     try:
    #         # Find the chat input field by ID and send a message
    #         chat_input = driver.find_element(By.ID, "chat-input")
    #         chat_input.send_keys("Hi, I need your help")
    #         chat_input.send_keys(Keys.ENTER)
    #
    #         # Wait for elements to load (adjust the time as needed)
    #         driver.implicitly_wait(15)
    #
    #         # Find the thumbs-up icon by XPath
    #         thumbs_up_icon = driver.find_element(By.XPATH, "//span[@aria-label='Not helpful']")
    #
    #         # Check if the thumbs-up icon is displayed
    #         assert thumbs_up_icon.is_displayed(), 'Thumbs DOWN not DISPLAYED'
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {str(e)}")
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_ChatBOtAvailibilityOnLogin(self, driver):
    #     try:
    #         # Find the chat input field by ID and send a message
    #         chat_input = driver.find_element(By.ID, "chat-input")
    #         # Check if the thumbs-up icon is displayed
    #         assert chat_input.is_displayed(), 'BOT is NOT available'
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {str(e)}")
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_Instructions(self, driver):
    #     try:
    #         # Find the chat input field by ID and send a message
    #         chat_input = driver.find_element(By.XPATH, "//div[@class='markdown-body']")
    #         # Check if the thumbs-up icon is displayed
    #         assert chat_input.is_displayed(), 'Instructions are displayed'
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {str(e)}")
    #         # Re-raise the exception to fail the test
    #
    # ##=================================Not completed below test-Need to complete once API is ready to delete history====================================================
    # # @pytest.mark.usefixtures("driver")
    # # def test_DeleteChatHistory(self, driver):
    # #     driver.implicitly_wait(15)
    # #     try:
    # #         driver.refresh()
    # #         driver.execute_script('return document.readyState;')
    # #         chatElements = driver.find_elements(By.XPATH,
    # #                                             f"//*[contains(text(), 'Today')]/following::a[starts-with(@id,'thread')]")
    # #         for element in chatElements:
    # #             driver.refresh()
    # #             driver.execute_script('return document.readyState;')
    # #             print("####################RAM##########################")
    # #             element.click()
    # #             # element.click()
    # #             driver.implicitly_wait(15)
    # #             element_to_hover_over = driver.find_element(By.XPATH, f"//a[starts-with(@id,'thread')]//button")
    # #
    # #             # Create an instance of ActionChains
    # #             actions = ActionChains(driver)
    # #
    # #             # Perform mouse hover over the element
    # #             actions.move_to_element(element_to_hover_over).perform()
    # #
    # #             # Wait for a short time, if needed
    # #             driver.implicitly_wait(15)
    # #
    # #             # Click on the element after the hover
    # #             element_to_hover_over.click()
    # #             # driver.execute_script("arguments[0].click();", element_to_hover_over)
    # #             print("####################HARI##########################")
    # #
    # #             driver.implicitly_wait(15)
    # #             driver.find_element(By.XPATH, f"//button[text()='Confirm']").click()
    # #             time.sleep(6)
    # #             driver.refresh()
    # #             time.sleep(6)
    # #             assert chatElements.count > 0, "Chat history deleted"
    # #
    # #     except Exception as e:
    # #         # Print the exception details for debugging
    # #         print(f"Exception occurred: {e}")
    # #         assert False
    # #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_KeepingInteractionRecordsHistory(self, driver):
    #     try:
    #         driver.implicitly_wait(15)
    #         chatElements = driver.find_elements(By.XPATH,
    #                                             f"//following::a[starts-with(@id,'thread')]")
    #         print("==========================================================")
    #         chatLengthBeforeAdd = len(chatElements)
    #         # Wait for a short time, if needed
    #         driver.implicitly_wait(15)
    #         # Click on the element after the hover
    #         chat_input = driver.find_element(By.ID, f"chat-input")
    #         ActionChains(driver).move_to_element(chat_input).click(chat_input).perform()
    #         # chat_input.click()
    #         chat_input.send_keys(f"Hi, I need your help")
    #         chat_input.send_keys(Keys.ENTER)
    #         driver.implicitly_wait(15)
    #         chat_input.send_keys(f"I need your help for personal care")
    #         chat_input.send_keys(Keys.ENTER)
    #         driver.find_element(By.XPATH, f"//img[contains(@class,'MuiAvatar')]").click()
    #         time.sleep(5)
    #         driver.find_element(By.XPATH, f"//ul[@role='menu']//li[contains(.,'Logout')]").click()
    #         login_button = driver.find_element(By.XPATH, f"//div[@class='MuiStack-root css-eb1amy']")
    #         login_button.click()
    #         driver.implicitly_wait(15)
    #         driver.find_element(By.XPATH, f"//input[@name='username']").send_keys(f"testing@cura.com")
    #         driver.find_element(By.NAME, f"action").click()
    #         driver.find_element(By.XPATH, f"//input[@name='password']").send_keys('eV030UqN')
    #         driver.find_element(By.NAME, f"action").click()
    #         driver.implicitly_wait(10)
    #         print("printing Title->", driver.title)
    #         assert driver.title == 'Cura'
    #         driver.refresh()
    #         driver.execute_script('return document.readyState;')
    #         chatElements1 = driver.find_elements(By.XPATH,
    #                                              f"//following::a[starts-with(@id,'thread')]")
    #         print("==========================================================")
    #         chatLengthAfterAdd = len(chatElements)
    #         assert chatLengthBeforeAdd == chatLengthAfterAdd, "Chat has NOT added to history"
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {e}")
    #         assert 0
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_DeleteOneChatHistory(self, driver):
    #     driver.implicitly_wait(15)
    #     try:
    #         chatElement = driver.find_element(By.XPATH,
    #                                           f"//*[contains(text(), 'Today')]/following::a[starts-with(@id,'thread')]")
    #         chatElements = driver.find_elements(By.XPATH,
    #                                             f"//*[contains(text(), 'Today')]/following::a[starts-with(@id,'thread')]")
    #         driver.implicitly_wait(3)
    #         print("####################RAM##########################")
    #         chatElement.click()
    #         # element.click()
    #         driver.implicitly_wait(15)
    #         element_to_hover_over = driver.find_element(By.XPATH, f"//a[starts-with(@id,'thread')]//button")
    #
    #         # Create an instance of ActionChains
    #         actions = ActionChains(driver)
    #
    #         # Perform mouse hover over the element
    #         actions.move_to_element(element_to_hover_over).perform()
    #
    #         # Wait for a short time, if needed
    #         driver.implicitly_wait(15)
    #
    #         # Click on the element after the hover
    #         element_to_hover_over.click()
    #         driver.execute_script("arguments[0].click();", element_to_hover_over)
    #         print("####################HARI##########################")
    #
    #         driver.implicitly_wait(15)
    #         driver.find_element(By.XPATH, f"//button[text()='Confirm']").click()
    #         driver.implicitly_wait(15)
    #         chatElementsafterdel = driver.find_elements(By.XPATH,
    #                                                     f"//*[contains(text(), 'Today')]/following::a[starts-with(@id,'thread')]")
    #         assert len(chatElements) == len(chatElementsafterdel), "Chat history deleted"
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {e}")
    #         assert 0
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_CorrectInstructions(self, driver):
    #     try:
    #         driver.execute_script('return document.readyState;')
    #         with open('instructions.txt', 'r', encoding="utf8") as file:
    #             contents = file.read()
    #         # Find the chat input field by ID and send a message
    #         chat_input = driver.find_element(By.XPATH, "//div[@class='markdown-body']")
    #         # Check if the thumbs-up icon is displayed
    #         print(chat_input.text)
    #         print(isinstance(chat_input.text, str))
    #         assert chat_input.text == contents, "NOT matching"
    #         # assert not chat_input.is_displayed(), 'Instructions are displayed'
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {str(e)}")
    #         assert 0
    #
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_EndChatButtonExistance(self, driver):
    #     try:
    #         # Find the chat input field by ID and send a message
    #         chat_input = driver.find_element(By.ID, "new-chat-button")
    #         # Check if the thumbs-up icon is displayed
    #         assert not chat_input.is_displayed(), 'End chat button is MISSING'
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {str(e)}")
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_EndChatButtonDialogExistance(self, driver):
    #     try:
    #         driver.execute_script('return document.readyState;')
    #         newChat = driver.find_element(By.ID, "new-chat-button")
    #         # Check if the thumbs-up icon is displayed
    #         newChat.click()
    #         endChatDialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
    #         assert endChatDialog.is_displayed(), 'End chat dialog is NOT displayed'
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {str(e)}")
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_EndChatAndConfirm(self, driver):
    #     try:
    #         # Find the chat input field by ID and send a message
    #         driver.execute_script('return document.readyState;')
    #         newChat = driver.find_element(By.ID, "new-chat-button")
    #         # Check if the thumbs-up icon is displayed
    #         newChat.click()
    #         driver.execute_script('return document.readyState;')
    #         endChatDialog = driver.find_element(By.XPATH, "// div[ @ role = 'dialog']")
    #         assert endChatDialog.is_displayed(), 'End chat dialog is NT displayed'
    #         btnConfirm = driver.find_element(By.ID, "confirm")
    #         btnConfirm.click()
    #         time.sleep(5)
    #         chat_input = driver.find_element(By.ID, f"chat-input")
    #         assert chat_input.is_displayed(), 'End chat closed and user landed to chat window'
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {str(e)}")
    #         assert 0
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_EndChatAndCancel(self, driver):
    #     try:
    #         # Find the chat input field by ID and send a message
    #         newChat = driver.find_element(By.ID, "new-chat-button")
    #         # Check if the thumbs-up icon is displayed
    #         newChat.click()
    #         driver.execute_script('return document.readyState;')
    #         endChatDialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
    #         assert endChatDialog.is_displayed(), 'End chat dialog is NT displayed'
    #         btnConfirm = driver.find_element(By.XPATH, "//button[text()='Cancel']")
    #         btnConfirm.click()
    #         time.sleep(2)
    #         driver.refresh()
    #         time.sleep(6)
    #         driver.execute_script('return document.readyState;')
    #         chat_input = driver.find_element(By.ID, f"chat-input")
    #         assert chat_input.is_displayed(), 'End chat closed and user landed to chat window'
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {str(e)}")
    #         assert 0
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_FeedbackDisplayedThumbsUP(self, driver):
    #     try:
    #         driver.implicitly_wait(15)
    #         chatElements = driver.find_elements(By.XPATH,
    #                                             f"//*[contains(text(), 'Today')]/following::a[starts-with(@id,'thread')]")
    #         print("==========================================================")
    #         print(len(chatElements))
    #         # Wait for a short time, if needed
    #         driver.implicitly_wait(15)
    #         # Click on the element after the hover
    #         chat_input = driver.find_element(By.ID, f"chat-input")
    #         ActionChains(driver).move_to_element(chat_input).click(chat_input).perform()
    #         # chat_input.click()
    #         # WebDriverWait(driver, 10).until(
    #         #     EC.visibility_of_element_located(chat_input))
    #         chat_input.send_keys(f"Hi, I need your help")
    #         chat_input.send_keys(Keys.ENTER)
    #         time.sleep(6)
    #         driver.implicitly_wait(15)
    #         driver.execute_script('return document.readyState;')
    #         element = WebDriverWait(driver, 15).until(
    #             EC.visibility_of_element_located((By.XPATH, "//span[@aria-label='Helpful']"))
    #         )
    #         time.sleep(5)
    #         # eleThumbUP=driver.find_element(By.XPATH, "//span[@aria-label='Helpful']")
    #         driver.find_element(By.XPATH, "//span[@aria-label='Helpful']").click()
    #
    #         driver.execute_script('return document.readyState;')
    #         time.sleep(5)
    #         feedbackDialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
    #         assert feedbackDialog.is_displayed(), "Dailog box NOT displayed"
    #
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {e}")
    #         assert 0
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_EnterFeeddbackHelpfull(self, driver):
    #     try:
    #         driver.implicitly_wait(15)
    #         chatElements = driver.find_elements(By.XPATH,
    #                                             f"//*[contains(text(), 'Today')]/following::a[starts-with(@id,'thread')]")
    #         print("==========================================================")
    #         print(len(chatElements))
    #         # Wait for a short time, if needed
    #         driver.implicitly_wait(15)
    #         # Click on the element after the hover
    #         chat_input = driver.find_element(By.ID, f"chat-input")
    #         ActionChains(driver).move_to_element(chat_input).click(chat_input).perform()
    #         # chat_input.click()
    #         # WebDriverWait(driver, 10).until(
    #         #     EC.visibility_of_element_located(chat_input))
    #         chat_input.send_keys(f"Hi, I need your help")
    #         chat_input.send_keys(Keys.ENTER)
    #         driver.implicitly_wait(15)
    #         driver.execute_script('return document.readyState;')
    #         element = WebDriverWait(driver, 15).until(
    #             EC.visibility_of_element_located((By.XPATH, "//span[@aria-label='Helpful']"))
    #         )
    #         time.sleep(5)
    #         # eleThumbUP=driver.find_element(By.XPATH, "//span[@aria-label='Helpful']")
    #         driver.find_element(By.XPATH, "//span[@aria-label='Helpful']").click()
    #
    #         driver.execute_script('return document.readyState;')
    #         time.sleep(5)
    #         feedbackDialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
    #         assert feedbackDialog.is_displayed(), "Dailog box NOT displayed"
    #         feedbackDialogInput = driver.find_element(By.ID, "feedbackDescription")
    #         feedbackDialogInput.send_keys("Happy")
    #         driver.find_element(By.ID, "feedbackSubmit").click()
    #         time.sleep(5)
    #         driver.execute_script('return document.readyState;')
    #         assert driver.find_element(By.XPATH,
    #                                    "//span[@aria-label='Feedback']").is_displayed(), "Feedback NOT submitted"
    #         print("Hey")
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {e}")
    #         assert 0
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_EnterFeeddbackNOTHelpfull(self, driver):
    #     try:
    #         driver.implicitly_wait(15)
    #         chatElements = driver.find_elements(By.XPATH,
    #                                             f"//*[contains(text(), 'Today')]/following::a[starts-with(@id,'thread')]")
    #         print("==========================================================")
    #         print(len(chatElements))
    #         # Wait for a short time, if needed
    #         driver.implicitly_wait(15)
    #         # Click on the element after the hover
    #         chat_input = driver.find_element(By.ID, f"chat-input")
    #         ActionChains(driver).move_to_element(chat_input).click(chat_input).perform()
    #         # chat_input.click()
    #         # WebDriverWait(driver, 10).until(
    #         #     EC.visibility_of_element_located(chat_input))
    #         chat_input.send_keys(f"Hi, I need your help")
    #         chat_input.send_keys(Keys.ENTER)
    #         driver.implicitly_wait(15)
    #         driver.execute_script('return document.readyState;')
    #         element = WebDriverWait(driver, 15).until(
    #             EC.visibility_of_element_located((By.XPATH, "//span[@aria-label='Not helpful']"))
    #         )
    #         time.sleep(5)
    #         # eleThumbUP=driver.find_element(By.XPATH, "//span[@aria-label='Helpful']")
    #         driver.find_element(By.XPATH, "(//span[@aria-label='Not helpful'])").click()
    #
    #         driver.execute_script('return document.readyState;')
    #         time.sleep(5)
    #         feedbackDialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
    #         assert feedbackDialog.is_displayed(), "Dailog box NOT displayed"
    #         feedbackDialogInput = driver.find_element(By.ID, "feedbackDescription")
    #         feedbackDialogInput.send_keys("NOT Happy")
    #         driver.find_element(By.ID, "feedbackSubmit").click()
    #         time.sleep(5)
    #         driver.execute_script('return document.readyState;')
    #         assert driver.find_element(By.XPATH,
    #                                    "//span[@aria-label='Feedback']").is_displayed(), "Feedback NOT submitted"
    #         time.sleep(5)
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {e}")
    #         assert 0
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_EnterFeedbackHelpfullConfirmMsg(self, driver):
    #     try:
    #         driver.implicitly_wait(15)
    #         chatElements = driver.find_elements(By.XPATH,
    #                                             f"//*[contains(text(), 'Today')]/following::a[starts-with(@id,'thread')]")
    #         print("==========================================================")
    #         print(len(chatElements))
    #         # Wait for a short time, if needed
    #         driver.implicitly_wait(15)
    #         # Click on the element after the hover
    #         chat_input = driver.find_element(By.ID, f"chat-input")
    #         ActionChains(driver).move_to_element(chat_input).click(chat_input).perform()
    #         # chat_input.click()
    #         # WebDriverWait(driver, 10).until(
    #         #     EC.visibility_of_element_located(chat_input))
    #         chat_input.send_keys(f"Hi, I need your help")
    #         chat_input.send_keys(Keys.ENTER)
    #         driver.implicitly_wait(15)
    #         driver.execute_script('return document.readyState;')
    #         element = WebDriverWait(driver, 15).until(
    #             EC.visibility_of_element_located((By.XPATH, "//span[@aria-label='Not helpful']"))
    #         )
    #         time.sleep(5)
    #         # eleThumbUP=driver.find_element(By.XPATH, "//span[@aria-label='Helpful']")
    #         driver.find_element(By.XPATH, "(//span[@aria-label='Helpful'])").click()
    #
    #         driver.execute_script('return document.readyState;')
    #         time.sleep(5)
    #         feedbackDialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
    #         assert feedbackDialog.is_displayed(), "Dailog box NOT displayed"
    #         feedbackDialogInput = driver.find_element(By.ID, "feedbackDescription")
    #         feedbackDialogInput.send_keys("NOT Happy")
    #         driver.find_element(By.ID, "feedbackSubmit").click()
    #         # time.sleep(5)
    #         # driver.execute_script('return document.readyState;')
    #         WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, "//li[@aria-live='polite']")))
    #         assert driver.find_element(By.XPATH,
    #                                    "//li[@aria-live='polite']").is_displayed(), "Feedback NOT submitted"
    #         time.sleep(5)
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {e}")
    #         assert 0
    #         # Re-raise the exception to fail the test
    #
    # @pytest.mark.usefixtures("driver")
    # def test_EnterFeedbackNOTHelpfullConfirmMsg(self, driver):
    #     try:
    #         driver.implicitly_wait(15)
    #         chatElements = driver.find_elements(By.XPATH,
    #                                             f"//*[contains(text(), 'Today')]/following::a[starts-with(@id,'thread')]")
    #         print("==========================================================")
    #         print(len(chatElements))
    #         # Wait for a short time, if needed
    #         driver.implicitly_wait(15)
    #         # Click on the element after the hover
    #         chat_input = driver.find_element(By.ID, f"chat-input")
    #         ActionChains(driver).move_to_element(chat_input).click(chat_input).perform()
    #         # chat_input.click()
    #         # WebDriverWait(driver, 10).until(
    #         #     EC.visibility_of_element_located(chat_input))
    #         chat_input.send_keys(f"Hi, I need your help")
    #         chat_input.send_keys(Keys.ENTER)
    #         driver.implicitly_wait(15)
    #         driver.execute_script('return document.readyState;')
    #         element = WebDriverWait(driver, 15).until(
    #             EC.visibility_of_element_located((By.XPATH, "//span[@aria-label='Not helpful']"))
    #         )
    #         time.sleep(5)
    #         # eleThumbUP=driver.find_element(By.XPATH, "//span[@aria-label='Helpful']")
    #         driver.find_element(By.XPATH, "(//span[@aria-label='Not helpful'])").click()
    #
    #         driver.execute_script('return document.readyState;')
    #         time.sleep(5)
    #         feedbackDialog = driver.find_element(By.XPATH, "//div[@role='dialog']")
    #         assert feedbackDialog.is_displayed(), "Dailog box NOT displayed"
    #         feedbackDialogInput = driver.find_element(By.ID, "feedbackDescription")
    #         feedbackDialogInput.send_keys("NOT Happy")
    #         driver.find_element(By.ID, "feedbackSubmit").click()
    #         # time.sleep(5)
    #         # driver.execute_script('return document.readyState;')
    #         WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, "//li[@aria-live='polite']")))
    #         assert driver.find_element(By.XPATH,
    #                                    "//li[@aria-live='polite']").is_displayed(), "Feedback NOT submitted"
    #         time.sleep(5)
    #     except Exception as e:
    #         # Print the exception details for debugging
    #         print(f"Exception occurred: {e}")
    #         assert 0
    #         # Re-raise the exception to fail the test
