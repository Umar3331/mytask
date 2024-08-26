from flask import Flask, request, jsonify
import telegram
import mysql.connector
import os
import asyncio
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

app = Flask(__name__)

# Setup Telegram Bot
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telegram.Bot(token=TOKEN)

# Database Connection
try:
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME')
    )
except mysql.connector.Error as err:
    print(f"Database connection error: {err}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
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
        cursor.execute("INSERT INTO users (name, surname, email, phone, invitation_number) VALUES (%s, %s, %s, %s, %s)", 
                       (name, surname, email, phone, invitation_number))
        db.commit()

        # Process booking via Selenium
        appointment_date = book_appointment(user_text)

        # Send confirmation message
        asyncio.run(bot.send_message(chat_id=chat_id, text=f"Appointment booked for: {appointment_date}"))
        return jsonify({"status": "success"}), 200

    except mysql.connector.Error as db_err:
        print(f"Database error: {db_err}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

def book_appointment(user_details):
    try:
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
        # Implement your Selenium logic here

        driver.quit()
        return "Appointment Booked Successfully"
    except Exception as e:
        print(f"Selenium error: {str(e)}")
        return "Failed to book the appointment"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

