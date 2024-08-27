from flask import Flask, request, jsonify
import telegram
import mysql.connector
import os
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from telegram.utils.request import Request as TelegramRequest  # Renamed to avoid conflict with Flask's request

app = Flask(__name__)

# Setup Telegram Bot with connection pool size
TOKEN = os.getenv('TELEGRAM_TOKEN')
tg_request = TelegramRequest(con_pool_size=10)  # Renamed to tg_request to avoid conflict with Flask's request
bot = telegram.Bot(token=TOKEN, request=tg_request)

# Database Connection Pool Setup
db = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASS'),
    database=os.getenv('DB_NAME'),
    pool_name="mypool",
    pool_size=10  # Adjust pool size as per your requirements
)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Use Flask's request object correctly
        data = request.get_json()  # Now this correctly refers to Flask's request object

        if 'message' not in data:
            return jsonify({"error": "'message' key not found"}), 400

        chat_id = data['message']['chat']['id']
        user_text = data['message']['text']

        # Assuming user input is comma-separated (name, surname, email, phone, invitation_number)
        try:
            name, surname, email, phone, invitation_number = [x.strip() for x in user_text.split(',')]
        except ValueError:
            return jsonify({"error": "Invalid input format. Please provide name, surname, email, phone, and invitation_number separated by commas."}), 400

        # Log user details in the database
        cursor = db.cursor()

        print(f"User Data: {name}, {surname}, {email}, {phone}, {invitation_number}")

        # Database query and commit
        try:
            cursor.execute("INSERT INTO users (name, surname, email, phone, invitation_number) VALUES (%s, %s, %s, %s, %s)",
                           (name, surname, email, phone, invitation_number))
            db.commit()
        except mysql.connector.Error as db_err:
            print(f"Database error: {db_err}")
            return jsonify({"error": f"Database error: {str(db_err)}"}), 500

        # Process booking via Selenium
        appointment_date = book_appointment(user_text)

        # Send confirmation message (synchronously)
        try:
            bot.send_message(chat_id=chat_id, text=f"Appointment booked for: {appointment_date}")
        except telegram.error.TelegramError as telegram_err:
            print(f"Telegram error: {telegram_err}")
            return jsonify({"error": f"Telegram Error: {str(telegram_err)}"}), 500

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

def book_appointment(user_details):
    try:
        # Connect to the remote Selenium container
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            desired_capabilities=DesiredCapabilities.CHROME,
            options=options
        )

        driver.get("https://pieraksts.mfa.gov.lv/en/uited-arab-emirates/index")
        # Implement Selenium logic here

        driver.quit()
        return "Appointment Booked Successfully"
    except Exception as e:
        print(f"Selenium error: {str(e)}")
        return "Failed to book the appointment"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

