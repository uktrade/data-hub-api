import os
from notifications_python_client.notifications import NotificationsAPIClient
from dotenv import load_dotenv

def get_env_variables():
    load_dotenv('.env')
    api_key = os.getenv('API_KEY')
    email_address = os.getenv('SENDER_EMAIL_ADDRESS')
    template_id = os.getenv('TEMPLATE_ID')
    return api_key, email_address, template_id

def send_email():
    try:
        api_key, email_address, template_id = get_env_variables()

        if not (api_key and email_address and template_id):
            print("Missing environment variables")
            return

        notifications_client = NotificationsAPIClient(api_key)
        
        response = notifications_client.send_email_notification(
            email_address=email_address,
            template_id=template_id,
        )
        
        # Handle the response as needed
        print("Email sent:", response)
    
    except Exception as e:
        print("An error occurred:", str(e))    

if __name__ == "__main__":
    send_email()