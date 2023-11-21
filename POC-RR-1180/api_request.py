import os
from notifications_python_client.notifications import NotificationsAPIClient
from dotenv import load_dotenv

def get_env_variables():
    load_dotenv('.env')
    api_key = os.getenv('API_KEY')
    email_address = os.getenv('SENDER_EMAIL_ADDRESS')
    template_id = os.getenv('TEMPLATE_ID')
    goods_services = os.getenv('GOODS_SERVICES')
    country_destination = os.getenv('COUNTRY_DESTINATION')
    client_firstname = os.getenv('CLIENT_FIRSTNAME')
    lead_officer_fullname = os.getenv('LEAD_OFFICER_FULLNAME')
    url_link= = os.getenv('URL')
    return api_key, email_address, template_id, goods_services, country_destination,client_firstname,lead_officer_fullname, url_link

def send_email():
    try:
        api_key, email_address, template_id = get_env_variables()

        if not (api_key and email_address and template_id):
            print("Missing environment variables")
            return

        notifications_client = NotificationsAPIClient(api_key)
        
        # personalisation info
        personalisation_data={
            'goods_services': goods_services,
            'country_destination': country_destination,
            'client_firstname': client_firstname,
            'lead_officer_fullname': lead_officer_fullname,
            'url': url_link,
        }

        response = notifications_client.send_email_notification(
            email_address=email_address,
            template_id=template_id,
            personalisation=personalisation_data,
        )
        
        # Handle the response as needed
        print("Email sent:", response)
    
    except Exception as e:
        print("An error occurred:", str(e))    

if __name__ == "__main__":
    send_email()