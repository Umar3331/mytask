# Use Python slim image as the base
FROM python:3.10-slim

# Install dependencies including netcat-openbsd, Chrome, and ChromeDriver
RUN apt-get update && apt-get install -y wget gnupg unzip netcat-openbsd \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update && apt-get install -y google-chrome-stable \
    && wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ && chmod +x /usr/local/bin/chromedriver \
    && apt-get install -y libnss3 libgconf-2-4 \
    && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy the app code into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir Flask selenium python-telegram-bot mysql-connector-python

# Run the application with wait-for-it script
CMD ["./wait-for-it.sh", "db:3306", "--", "python", "app/main.py"]

