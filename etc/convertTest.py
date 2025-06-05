from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import time

options = Options()
options.headless = True
options.add_argument('--window-size=1200x800')

driver = webdriver.Chrome(options=options)
driver.get("data:text/html,<html><body><h1>Hello World</h1><p>This is a rendered image</p></body></html>")

# wait for rendering
time.sleep(1)

driver.save_screenshot("screenshot.png")
driver.quit()

# (optional) crop or convert using PIL
img = Image.open("screenshot.png")
img = img.crop((0, 0, 800, 600))  # crop if needed
img.save("output.png")