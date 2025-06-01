from behave import step
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

@step('Navigate to Google')
def step_impl(context):
    service = ChromeService(ChromeDriverManager().install())
    context.driver = webdriver.Chrome(service=service)
    context.driver.get("https://www.google.com")
