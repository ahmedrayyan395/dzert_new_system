import json
import requests
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Variables
last_sent_status = None
# Define the product name variable
product_name_variable = "تمره"
# Path to the image on your desktop
image_path = "C:\\Users\\Administrator\\Desktop\\tamra.png"
buttons_clicked = False

def find_element_with_retries(driver, by, value, retries=3, delay=1):
    attempt = 0
    while attempt < retries:
        try:
            element = driver.find_element(by, value)
            return element
        except NoSuchElementException:
            attempt += 1
            if attempt == retries:
                raise
            time.sleep(delay)

def handle_initial_buttons(driver):
    global buttons_clicked
    if not buttons_clicked:
        try:
            # Click the age verification button
            try:
                age_verification_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='18 سنة أو أكثر']"))
                )
                age_verification_button.click()
            except TimeoutException:
                print("Failed to find the age verification button.")

            # Click the cookie consent button
            try:
                cookie_consent_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='قبول جميع ملفات تعريف الارتباط']"))
                )
                cookie_consent_button.click()
            except TimeoutException:
                print("Failed to find the cookie consent button.")

            buttons_clicked = True
        except Exception as e:
            print(f"Error handling initial buttons: {str(e)}")

def fetch_product_details_with_selenium(driver, product_url):
    driver.get(product_url)
    try:
        # Handle initial buttons only once
        handle_initial_buttons(driver)

        # Extract product name
        product_name = product_name_variable

        # Check if the "Add to Cart" button is not disabled
        try:
            add_to_cart_button = find_element_with_retries(
                driver, By.XPATH, "//button[contains(text(), 'اضف الى السلة')]"
            )
            if add_to_cart_button.is_enabled():
                product_status = "متوفر"
            else:
                product_status = "نفذ من المخزون"
        except Exception as e:
            product_status = "نفذ من المخزون"

        return product_name, product_status
    except Exception as e:
        print(f"Error extracting product details for {product_url}: {str(e)}")
        return None, None

def send_product_data_to_telegram(product_name, product_status, product_link):
    bot_token = "7578015058:AAFSfVOIUiDTv6ymrGF062MCGyYWl0aFpUo"
    chat_id = "-1002415104525"



    telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    # Update message text with emojis and formatting
    if product_status == "متوفر":
        message_text = f"✅ **المنتج متاح** ✅: {product_name}"
        RLM = '\u200F'  # Right-to-Left Mark
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": f"🔍 عرض المنتج {RLM}", "url": product_link},
                    {"text": f"🛒 عرض السلة {RLM}", "url": "https://www.dzrt.com/ar-sa/cart"}
                ],
                [
                    {"text": f"🔐تسجيل الدخول {RLM}", "url": "https://www.dzrt.com/ar-sa/login"},
                    {"text": f"💳 الدفع  {RLM}", "url": "https://www.dzrt.com/ar-sa/checkout"}
                ]
            ]
        }
    else:
        message_text = f"❌ **نفذ من المخزون** ❌: {product_name}"
        reply_markup = {
            "inline_keyboard": [
                [{"text": "🔐 تسجيل الدخول", "url": "https://www.dzrt.com/ar/customer/account/login/"}]
            ]
        }

    # Send the message with image
    with open(image_path, 'rb') as image_file:
        files = {'photo': image_file}
        params = {
            "chat_id": chat_id,
            "caption": message_text,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(reply_markup)
        }
        response = requests.post(telegram_api_url, files=files, data=params)
        if response.status_code == 200:
            print(f"Product data sent successfully for {product_name}")
        else:
            print(f"Failed to send product data for {product_name}. Status code: {response.status_code}")

def main():
    global last_sent_status
    url = "https://www.dzrt.com/ar-sa/products/tamra"
    
    # Configure Chrome options
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--lang=ar')
    options.add_argument('--disable-dev-shm-usage')

    # Initialize the driver
    driver = uc.Chrome(options=options)

    try:
        while True:
            product_name, product_status = fetch_product_details_with_selenium(driver, url)
            if product_name and product_name == product_name_variable:
                # Check if the product status has changed
                if product_status != last_sent_status:
                    send_product_data_to_telegram(product_name, product_status, url)
                    last_sent_status = product_status
            # Wait before next check
            time.sleep(1)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()