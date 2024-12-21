import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def send_email(to_email: str, name: str):
    from_email = os.getenv('MAIL_FROM')
    from_password = os.getenv('MAIL_PASSWORD')  

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Welcome to Mindspace!"

    html = f"""
    <html>
        <body>
            <h2>Welcome to Mindspace, {name}!</h2>
            <p>You have successfully registered to the Mindspace app.</p>
            <p>Thank you for joining us!</p>
        </body>
    </html>
    """

    msg.attach(MIMEText(html, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        server.login(from_email, from_password)
        
        server.send_message(msg)
        print(f"Email sent successfully to {to_email}")
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        
    finally:
        server.quit()
