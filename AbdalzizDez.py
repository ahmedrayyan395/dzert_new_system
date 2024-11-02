import os
import requests
import json
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Retrieve the 2Captcha API key from environment variables or a secure source
captcha_api_key = "22b8a18d3bb7d50190ee5867bbcffc0d"


def verify_captcha_api_key(api_key):
    """Verify the 2Captcha API key by checking the account balance."""
    try:
        response = requests.get(f"http://2captcha.com/res.php?key={api_key}&action=getbalance&json=1")
        result = response.json()
        if response.status_code == 200 and 'status' in result and result['status'] == 1:
            print(f"API key is valid. Current balance: {result['request']}")
            return True
        else:
            print(f"Invalid API key or error: {result.get('request', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"Error verifying API key: {e}")
        return False

# Verify the API key before proceeding
if not captcha_api_key or not verify_captcha_api_key(captcha_api_key):
    print("Exiting the script due to invalid 2Captcha API key.")
    exit()

# Your existing script logic
# Global list to store product names that are successfully sent
sent_products = []
# Dictionary to store the time each product was last sent
product_send_times = {}
# List of products that have special handling
special_products = ["بيربل مست", "هايلاند بيريز", "سبايسي زيست"]
# List of products to exclude from sending
excluded_products = []
# Variable to store the time of the last clearing of the sent_products list
last_clear_time = time.time()
# Product URL to name mapping
product_url_to_name = {
    "https://www.dzrt.com/products/icy-rush": "ايسي رش",
    "https://www.dzrt.com/products/garden-mint": "جاردن منت",
    "https://www.dzrt.com/products/purple-mist": "بيربل مست",
    "https://www.dzrt.com/products/edgy-mint": "ايدجي منت",
    "https://www.dzrt.com/products/spicy-zest": "سبايسي زيست",
    "https://www.dzrt.com/products/mint-fusion": "منت فيوجن",
    "https://www.dzrt.com/products/seaside-frost": "سي سايد فروست",
    "https://www.dzrt.com/products/tamra": "تمرة",
    "https://www.dzrt.com/products/samra": "سمرة",
    "https://www.dzrt.com/products/haila": "هيلة",
    "https://www.dzrt.com/products/highland-berries": "هايلاند بيريز",
    "https://www.dzrt.com/products/samra-special-edition": "سمرة خاص"
}

# Set up undetected Chrome driver
options = uc.ChromeOptions()
options.add_argument("--headless")
driver = uc.Chrome(options=options)

def send_product_data_to_telegram():
    global sent_products, last_clear_time, product_send_times
    # Navigate to the page
    driver.get("https://www.dzrt.com/ar-sa/products")
    time.sleep(5)  # Wait for the page to load

    # Handle age verification
    try:
        age_verification_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='18 سنة أو أكثر']"))
        )
        age_verification_button.click()
    except TimeoutException:
        print("Failed to find the age verification button.")
        return

    # Handle cookie consent
    try:
        cookie_consent_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='قبول جميع ملفات تعريف الارتباط']"))
        )
        cookie_consent_button.click()
    except TimeoutException:
        print("Failed to find the cookie consent button.")
        return

    while True:
        driver.refresh()
        time.sleep(5)
        try:
            product_divs = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".relative.bg-white.px-2\\.5.pb-3.pt-6"))
            )
        except:
            print("Error finding the element .....")
            continue

        product_data_list = []
        for product_div in product_divs:
            try:
                # Function to find an element with retries
                def find_element_with_retries(driver, locator, retries=3, timeout=10):
                    attempt = 0
                    while attempt < retries:
                        try:
                            element = WebDriverWait(driver, timeout).until(
                                EC.presence_of_element_located(locator)
                            )
                            return element
                        except TimeoutException:
                            attempt += 1
                            if attempt == retries:
                                raise

                # Wait for the "Add to Cart" button and check if it's disabled
                try:
                    add_to_cart_button = find_element_with_retries(
                        product_div, (By.XPATH, ".//button[contains(text(), 'اضف الى السلة')]")
                    )
                    is_disabled = driver.execute_script("return arguments[0].hasAttribute('disabled');", add_to_cart_button)
                    product_status = "متوفر" if not is_disabled else "غير متوفر"
                except TimeoutException:
                    print("Failed to find the 'Add to Cart' button after 3 attempts.")

                # Wait for the image tag and get its URL
                try:
                    image_tag = find_element_with_retries(product_div, (By.CSS_SELECTOR, "img"))
                    image_url = image_tag.get_attribute('src') if image_tag else None
                except TimeoutException:
                    print("Failed to find the image tag after 3 attempts.")
                    image_url = None

                # Wait for the product link and get its URL
                try:
                    product_url_element = find_element_with_retries(product_div, (By.TAG_NAME, "a"))
                    product_url = product_url_element.get_attribute('href')
                except TimeoutException:
                    print("Failed to find the product link after 3 attempts.")
                    product_url = None

                # Use the product name from the URL mapping
                product_name = product_url_to_name.get(product_url)

                # Add product information to the list
                if product_name and product_status:
                    product_info = {
                        "name": product_name,
                        "status": product_status,
                        "image_url": image_url,
                        "url": product_url
                    }
                    product_data_list.append(product_info)
                    # Print product information
                    print(f"Product Name: {product_name}")
                    print(f"Product Status: {product_status}")
                    print(f"Image URL: {image_url}")
                    print("-" * 50)
            except Exception as e:
                print(f"Error processing product: {e}")

        # Define Telegram bot token and chat ID
        #bot_token = "6681933065:AAFvenDcv4yaiUEVAv4tjtsThKLgGRPux2A"
        #chat_id = "-1002120587144"
        

        #raay
        bot_token = "7971853493:AAECK1n2uf7iByMunIdHZheD1to2zIXoYPs"
        chat_id = "-1002381021374"



        telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

        for product_data in product_data_list:
            product_name = product_data.get("name", "")
            product_status = product_data.get("status", "")
            product_url = product_data.get("url", "")
            image_url = product_data.get("image_url", "")

            if product_status == "متوفر" and product_name not in excluded_products:
                current_time = time.time()
                if product_name in product_url_to_name.values():
                    if (product_name not in sent_products) or (current_time - product_send_times.get(product_name, 0) >= (3 * 6000)):
                        message_text = f"✅ ** المنتج متاح ** ✅: {product_name}"
                        RLM = '\u200F'  # Right-to-Left Mark

                        reply_markup = {
    "inline_keyboard": [
        [
            {"text": f"🔍 عرض المنتج {RLM}", "url": product_url},
            {"text": f"🛒 عرض السلة {RLM}", "url": "https://www.dzrt.com/ar-sa/cart"}
        ],
        [
            {"text": f"🔐تسجيل الدخول {RLM}", "url": "https://www.dzrt.com/ar-sa/login"},
            {"text": f"💳 الدفع  {RLM}", "url": "https://www.dzrt.com/ar-sa/checkout"}
        ]
    ]
}
                        params = {
                            "chat_id": chat_id,
                            "photo": image_url,
                            "caption": message_text,
                            "reply_markup": json.dumps(reply_markup)
                        }
                        response = requests.post(telegram_api_url, params=params)
                        if response.status_code == 200:
                            print(f"Product data sent successfully for {product_name}")
                            sent_products.append(product_name)
                            product_send_times[product_name] = current_time
                        else:
                            print(f"Failed to send product data for {product_name}. Status code: {response.status_code}")
                else:
                    if product_name not in sent_products:
                        message_text = f"✅ ** المنتج متاح ** ✅: {product_name}"
                        reply_markup = {
                             "inline_keyboard": [
                                [{"text": "🔍 عرض المنتج", "url": product_url}, {"text": "🛒 عرض السلة", "url": "https://www.dzrt.com/ar/checkout/cart"}],
                                [{"text": "🔐 تسجيل الدخول", "url": "https://www.dzrt.com/ar-sa/login"}, {"text": "💳 الانتقال إلى رابط الدفع النهائي", "url": "https://www.dzrt.com/ar-sa/checkout"}]
                            ]
                        }
                        params = {
                            "chat_id": chat_id,
                            "photo": image_url,
                            "caption": message_text,
                            "reply_markup": json.dumps(reply_markup)
                        }
                        response = requests.post(telegram_api_url, params=params)
                        if response.status_code == 200:
                            print(f"Product data sent successfully for {product_name}")
                            sent_products.append(product_name)
                        else:
                            print(f"Failed to send product data for {product_name}. Status code: {response.status_code}")

        if time.time() - last_clear_time >= 120:
            sent_products = [product for product in sent_products if product in special_products]
            last_clear_time = time.time()

        time.sleep(1)  # Check every 10 seconds

try:
    send_product_data_to_telegram()
finally:
    driver.quit()
