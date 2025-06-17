import requests
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import logging
import os
from dotenv import load_dotenv
import random

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EndpointPoller:
    def __init__(
        self,
        endpoint_url: str,
        gmail_user: str,
        gmail_password: str,
        recipient_email: str,
        poll_interval: int = 60
    ):
        self.endpoint_url = endpoint_url
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
        self.recipient_email = recipient_email
        self.poll_interval = poll_interval
        self.last_state_available = False

    def poll_endpoint(self) -> Optional[Dict[str, Any]]:
        """Poll the endpoint and return the response if it has non-zero content."""
        try:
            response = requests.get(self.endpoint_url)
            response.raise_for_status()
            
            if response.content and len(response.json()) > 0:
                return response.json()
            return None
        except requests.RequestException as e:
            logger.error(f"Error polling endpoint: {e}")
            return None

    def send_email(self, subject: str, body: str) -> bool:
        """Send an email using Gmail SMTP."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.gmail_user
            msg['To'] = self.recipient_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_user, self.gmail_password)
                server.send_message(msg)
            
            logger.info("Email sent successfully")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def start_polling(self):
        """
        Start polling the endpoint and send email when appointment becomes available.
        Only sends a new email when status changes from unavailable to available.
        """
        logger.info(f"Starting to poll {self.endpoint_url}")
        
        while True:
            response_data = self.poll_endpoint()
            currently_available = response_data is not None
            
            # Check if status changed from unavailable to available
            if currently_available and not self.last_state_available:
                subject = "Lulu Lemon Appointment Available"
                body = f"Appointment now available at {self.endpoint_url}:\n\n{response_data}"
                
                if self.send_email(subject, body):
                    logger.info("Email notification sent successfully")
            
            # Update the last state
            self.last_state_available = currently_available
            
            # Log the current status
            if currently_available:
                logger.info("Appointment is available")
            else:
                logger.info("No appointment available")
            
            # Add randomization to the polling interval
            jitter = random.uniform(-0.1, 0.1)  # Random value between -0.1 and 0.1
            sleep_time = self.poll_interval * (1 + jitter)
            logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

def get_required_env_var(name: str) -> str:
    """Get a required environment variable or raise an error if it's not set."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value

if __name__ == "__main__":
    try:
        # Get configuration from environment variables
        GMAIL_USER = get_required_env_var('GMAIL_USER')
        GMAIL_PASSWORD = get_required_env_var('GMAIL_PASSWORD')
        RECIPIENT_EMAIL = get_required_env_var('RECIPIENT_EMAIL')
        ENDPOINT_URL = get_required_env_var('ENDPOINT_URL')
        
        # Get poll interval from environment variable, defaulting to 60 if not set
        POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '60'))
        
        poller = EndpointPoller(
            endpoint_url=ENDPOINT_URL,
            gmail_user=GMAIL_USER,
            gmail_password=GMAIL_PASSWORD,
            recipient_email=RECIPIENT_EMAIL,
            poll_interval=POLL_INTERVAL
        )
        
        poller.start_polling()
    except ValueError as e:
        logger.error(str(e))
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1) 