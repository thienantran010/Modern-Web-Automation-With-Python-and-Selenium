from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
options.headless = True
assert options.headless

driver = Firefox(options=options)
driver.get('https://duckduckgo.com')

search_form = driver.find_element(By.ID, 'search_form_input_homepage')
search_form.send_keys('real python' + Keys.ENTER)

results = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'E2eLOJr8HctVnDOTM8fs')))
assert results
print(results[0].text)

driver.quit()