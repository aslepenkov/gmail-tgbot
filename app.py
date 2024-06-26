import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import requests
import schedule
import time
import configparser

# Read secrets from a configuration file
config = configparser.ConfigParser()
config.read("secrets.ini")

# Fetch the ID and BotToken from the configuration file
tgId = config["Telegram"]["ID"]
telegramBotToken = config["Telegram"]["BotToken"]

# Constants
last_run_time = datetime.now(timezone(timedelta(hours=+0))) - timedelta(days=1)
telegramMessage = ""

# Gmail API credentials
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
creds = None
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
    with open("token.json", "w") as token:
        print(creds.to_json())
        token.write(creds.to_json())

service = build("gmail", "v1", credentials=creds)
print("service built succesfully")

# Set up Telegram message parameters
def setTelegramMessageParams(subject, ffrom, body):
    global telegramMessage
    telegramMessage = f"*Subject:*\n{subject}\n*From:*\n{ffrom}\n*Body:*\n{body}"


# Fetch emails and send Telegram message
def fetchEmailsAndSendMessage():
    global last_run_time
    try:
        emailSearchQuery = f"after:{last_run_time.strftime('%Y/%m/%d')} is:unread"
        results = service.users().messages().list(userId='me', q=emailSearchQuery).execute()
        messages = results.get('messages', [])
        if messages:
            for message in messages:
                emailMessage = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
                headers = emailMessage['payload']['headers']
                for d in headers:
                    name = d['name']
                    if name == 'Subject':
                        subject = d['value']
                    if name == 'From':
                        ffrom = d['value']
                    if name.lower() == 'date':
                        email_date = datetime.strptime(d['value'], "%a, %d %b %Y %H:%M:%S %z")

                if email_date < last_run_time:
                    continue  # Skip this email if it was received before the last run time
                body = emailMessage['snippet']
                setTelegramMessageParams(subject, ffrom, body)
                sendTelegramMessage(telegramMessage)
        last_run_time = datetime.now(timezone(timedelta(hours=+0)))
    except:
        print("err")

# Send Telegram message
def sendTelegramMessage(message):
    telegramUrl = f"https://api.telegram.org/bot{telegramBotToken}/sendMessage"
    telegramPayload = {"chat_id": tgId, "text": message}
    response = requests.post(telegramUrl, json=telegramPayload)
    if response.status_code != 200:
        print(f"Failed to send Telegram message: {response.content} - {telegramUrl}")


# Schedule the fetchEmailsAndSendMessage function to run every 5 minutes
schedule.every(5).minutes.do(fetchEmailsAndSendMessage)


print(f"START APP GMAIL-BOT")
# Run the scheduled tasks indefinitely
while True:
    schedule.run_pending()
    time.sleep(60)
