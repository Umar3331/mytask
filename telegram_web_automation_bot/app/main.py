from flask import Flask, request, jsonify
import telegram
import mysql.connector
import os
from telegram.utils.request import Request as TelegramRequest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.remote.webdriver import WebDriver
import time
import logging
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Setup Telegram Bot with connection pool size
TOKEN = os.getenv('TELEGRAM_TOKEN')
tg_request = TelegramRequest(con_pool_size=10)
bot = telegram.Bot(token=TOKEN, request=tg_request)

# Database Connection Pool Setup
db = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASS'),
    database=os.getenv('DB_NAME'),
    pool_name="mypool",
    pool_size=10
)

# Function to create the user_states table if it doesn't exist
def create_tables():
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_states (
            chat_id BIGINT PRIMARY KEY,
            step INT,
            name VARCHAR(255),
            surname VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(255),
            invitation_number VARCHAR(255)
        );
    """)
    db.commit()
    cursor.close()

# Call the create_tables function at startup
create_tables()

def get_user_state(chat_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_states WHERE chat_id = %s", (chat_id,))
    result = cursor.fetchone()
    cursor.close()
    return result

def update_user_state(chat_id, step, name=None, surname=None, email=None, phone=None, invitation_number=None):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO user_states (chat_id, step, name, surname, email, phone, invitation_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        step = VALUES(step), name = VALUES(name), surname = VALUES(surname), email = VALUES(email), phone = VALUES(phone), invitation_number = VALUES(invitation_number)
    """, (chat_id, step, name, surname, email, phone, invitation_number))
    db.commit()
    cursor.close()

def clear_user_state(chat_id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM user_states WHERE chat_id = %s", (chat_id,))
    db.commit()
    cursor.close()

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()

        if 'message' not in data:
            return jsonify({"error": "'message' key not found"}), 400

        chat_id = data['message']['chat']['id']
        user_text = data['message']['text'].strip()

        # Handle the /start command
        if user_text.lower() == "/start":
            clear_user_state(chat_id)
            bot.send_message(chat_id, "Welcome! Let's start from the beginning. Please provide your name.")
            update_user_state(chat_id, step=1)
            return jsonify({"status": "ok"})

        # Retrieve or initialize the user's state from the database
        current_state = get_user_state(chat_id)
        if current_state is None:
            bot.send_message(chat_id, "It looks like we haven't started yet. Please type /start to begin.")
            return jsonify({"status": "ok"})

        step = current_state['step']

        # Process the user's input based on the current step
        if step == 1:
            bot.send_message(chat_id, "Please provide your surname.")
            update_user_state(chat_id, step=2, name=user_text)

        elif step == 2:
            bot.send_message(chat_id, "Please provide your email.")
            update_user_state(chat_id, step=3, name=current_state['name'], surname=user_text)

        elif step == 3:
            bot.send_message(chat_id, "Please confirm your email by typing it again.")
            update_user_state(chat_id, step=4, name=current_state['name'], surname=current_state['surname'], email=user_text)

        elif step == 4:
            if current_state['email'] != user_text:
                bot.send_message(chat_id, "Emails do not match. Let's start over. Please provide your name.")
                clear_user_state(chat_id)
                update_user_state(chat_id, step=1)
            else:
                bot.send_message(chat_id, "Please provide your phone number (with country code).")
                update_user_state(chat_id, step=5, name=current_state['name'], surname=current_state['surname'], email=current_state['email'])

        elif step == 5:
            bot.send_message(chat_id, "Please provide your invitation number.")
            update_user_state(chat_id, step=6, name=current_state['name'], surname=current_state['surname'], email=current_state['email'], phone=user_text)

        elif step == 6:
            bot.send_message(chat_id, "Thank you! Submitting your information...")

            # Final update with all data
            update_user_state(chat_id, step=7, name=current_state['name'], surname=current_state['surname'], email=current_state['email'], phone=current_state['phone'], invitation_number=user_text)

            # After collecting all data, book the appointment via Selenium
            book_appointment(current_state['name'], current_state['surname'], current_state['email'], current_state['phone'], user_text)
            
            bot.send_message(chat_id, "Your information has been submitted successfully.")
            clear_user_state(chat_id)

        return jsonify({"status": "ok"})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


def book_appointment(name, surname, email, phone, invitation_number):
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Optional: run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    logging.info("Starting Chrome WebDriver...")
    
    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )

    try:
        # Step 1: Go to the website
        logging.info("Navigating to the appointment website...")
        driver.get("https://pieraksts.mfa.gov.lv/en/uited-arab-emirates/index")
        time.sleep(2)
        logging.info("Website loaded successfully.")
        
        # Step 2: Fill in user details
        logging.info("Filling in user details: Name: %s, Surname: %s, Email: %s, Phone: %s", name, surname, email, phone)
        driver.find_element(By.NAME, 'name').send_keys(name)
        driver.find_element(By.NAME, 'surname').send_keys(surname)
        driver.find_element(By.NAME, 'email').send_keys(email)
        driver.find_element(By.NAME, 'email_repeat').send_keys(email)
        driver.find_element(By.NAME, 'phone').send_keys(phone)

        # Step 3: Click "Next"
        logging.info("Clicking 'Next' button...")
        driver.find_element(By.XPATH, "//button[text()='Next']").click()
        time.sleep(2)

        # Step 4: Select service
        logging.info("Selecting service: 'Residence permit request - STUDENTS'")
        select = Select(driver.find_element(By.NAME, 'service'))
        select.select_by_visible_text('Residence permit request - STUDENTS')
        time.sleep(2)

        # Step 5: Check the confirmation box and click 'Add'
        logging.info("Checking confirmation box and clicking 'Add'...")
        driver.find_element(By.XPATH, "//input[@type='checkbox']").click()
        driver.find_element(By.XPATH, "//button[text()='Add']").click()
        time.sleep(2)

        # Step 6: Proceed to next step
        logging.info("Clicking 'Next Step' button...")
        driver.find_element(By.XPATH, "//button[text()='Next Step']").click()
        time.sleep(2)

        # Step 7: Selecting earliest available date (placeholder logic)
        # TODO: Add logic for selecting the earliest available date
        logging.info("Selecting the earliest available date... (placeholder logic)")

        # Step 8: Enter invitation number
        logging.info("Entering invitation number: %s", invitation_number)
        driver.find_element(By.NAME, 'invitation_number').send_keys(invitation_number)

        # Step 9: Submit the form
        logging.info("Submitting the appointment form...")
        driver.find_element(By.XPATH, "//button[text()='Submit']").click()

        logging.info("Appointment successfully booked!")

    except Exception as e:
        logging.error("Error during appointment booking: %s", str(e))

    finally:
        logging.info("Closing Chrome WebDriver...")
        driver.quit()

@app.route('/test_selenium', methods=['GET'])
def test_selenium():
    try:
        # Set Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run Chrome in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Start the WebDriver
        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options  # Use options instead of desired_capabilities
        )
        
        # Visit Google
        driver.get("https://www.google.com")
        
        # Print page title to Flask logs
        print(driver.title)
        
        # Take a screenshot for verification
        driver.save_screenshot('/app/screenshots/test_selenium.png')
        
        # Close the driver
        driver.quit()
        
        return jsonify({"status": "Selenium test completed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
