import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
import config 

def send_email_after_register(email,subject, message):
   from_email = config.GMAIL_FROM
   from_password = config.GMAIL_PASSWORD
   to_email = email

   message = f"""
   <h1>Привет, {email}!</h1>
   <p>Ты успешно зарегистрировался в MindSpace.</p>
   <p>Теперь ты можешь начать использовать нашу платформу для управления задачами и проектами.</p>
   <p>Если у тебя возникнут вопросы или нужна помощь, обращайся к нам.</p>
   <p>Спасибо, что выбрал MindSpace!</p>
   """

   msg = MIMEText(message, 'html')
   msg['Subject'] = subject
   msg['To'] = to_email
   msg['From'] = from_email


   gmail = smtplib.SMTP('smtp.gmail.com', 587)
   gmail.ehlo()
   gmail.starttls()
   gmail.login(from_email, from_password)
   gmail.send_message(msg)


def send_email_before_deadline(email,subject, message):
   from_email = "mindspace228@gmail.com"
   from_password = "Palma1234!"
   to_email = email

   msg = MIMEText(message, 'html')
   msg['Subject'] = subject
   msg['To'] = to_email
   msg['From'] = from_email


async def check_and_send_notifications(session: AsyncSession):
    """
    Check for pending notifications and send them
    """
    try:
        # Get all unsent notifications that are due
        query = (
            select(Notification)
            .where(
                Notification.scheduled_time <= datetime.now(),
                Notification.sent == False
            )
        )
        result = await session.execute(query)
        notifications = result.scalars().all()
        
        for notification in notifications:
            # Send email
            send_email_before_deadline(
                notification.email,
                notification.subject,
                notification.message
            )
            
            # Mark as sent
            notification.sent = True
            
        await session.commit()
    except Exception as e:
        print(f"An error occurred while sending notifications: {e}")

