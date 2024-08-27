from flask import Flask, request, jsonify
import telegram
import mysql.connector
import os
from telegram.utils.request import Request as TelegramRequest

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
            # Store the name and move to the next step
            bot.send_message(chat_id, "Please provide your surname.")
            update_user_state(chat_id, step=2, name=user_text)
        
        elif step == 2:
            # Store the surname and move to the next step
            bot.send_message(chat_id, "Please provide your email.")
            update_user_state(chat_id, step=3, name=current_state['name'], surname=user_text)
        
        elif step == 3:
            # Store the email and ask for confirmation
            bot.send_message(chat_id, "Please confirm your email by typing it again.")
            update_user_state(chat_id, step=4, name=current_state['name'], surname=current_state['surname'], email=user_text)
        
        elif step == 4:
            # Confirm the email
            if current_state['email'] != user_text:
                bot.send_message(chat_id, "Emails do not match. Let's start over. Please provide your name.")
                clear_user_state(chat_id)
                update_user_state(chat_id, step=1)
            else:
                bot.send_message(chat_id, "Please provide your phone number (with country code).")
                update_user_state(chat_id, step=5, name=current_state['name'], surname=current_state['surname'], email=current_state['email'])
        
        elif step == 5:
            # Store the phone number and move to the next step
            bot.send_message(chat_id, "Please provide your invitation number.")
            update_user_state(chat_id, step=6, name=current_state['name'], surname=current_state['surname'], email=current_state['email'], phone=user_text)
        
        elif step == 6:
            # Store the invitation number, submit the data, and clear the state
            bot.send_message(chat_id, "Thank you! Submitting your information...")
            
            # Final update with all data
            update_user_state(chat_id, step=7, name=current_state['name'], surname=current_state['surname'], email=current_state['email'], phone=current_state['phone'], invitation_number=user_text)

            # Store data in the final users table (this assumes you have another table to store completed users)
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO users (name, surname, email, phone, invitation_number) VALUES (%s, %s, %s, %s, %s)",
                (current_state['name'], current_state['surname'], current_state['email'], current_state['phone'], user_text)
            )
            db.commit()
            cursor.close()

            bot.send_message(chat_id, "Your information has been submitted successfully.")
            
            # Clear user state after submission
            clear_user_state(chat_id)
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
