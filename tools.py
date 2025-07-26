import os
import smtplib
import requests
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from livekit.agents import function_tool, RunContext
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        return response.text.strip() if response.status_code == 200 else f"Could not retrieve weather for {city}."
    except Exception as e:
        return f"An error occurred while retrieving weather for {city}: {str(e)}"

@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        search_engine_id = os.getenv("GOOGLE_CSE_ID")

        if not api_key or not search_engine_id:
            return "Google Search API credentials are missing."

        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=search_engine_id).execute()

        if "items" not in res:
            return "No search results found."

        results = res["items"]
        return "\n".join([f"{item['title']}: {item['link']}" for item in results[:3]])
    except Exception as e:
        return f"An error occurred while searching the web for '{query}': {str(e)}"

@function_tool()
async def send_email(context: RunContext, to_email: str, subject: str, message: str, cc_email: Optional[str] = None) -> str:
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_password:
            return "Email sending failed: Gmail credentials not configured."

        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        recipients = [to_email]

        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)

        msg.attach(MIMEText(message, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, msg.as_string())
        server.quit()

        return f"Email sent successfully to {to_email}"
    except smtplib.SMTPAuthenticationError:
        return "Email sending failed: Authentication error."
    except smtplib.SMTPException as e:
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        return f"An error occurred while sending email: {str(e)}"
