import smtplib
from email.mime.text import MIMEText

def send_email(email,subject, message):
   from_email = "mindspace228@gmail.com"
   from_password = "Palma1234!"
   to_email = email

   msg = MIMEText(message, 'html')
   msg['Subject'] = subject
   msg['To'] = to_email
   msg['From'] = from_email


   # Create SMTP session for sending the mail
   gmail = smtplib.SMTP('smtp.gmail.com', 587)
   gmail.ehlo()
   gmail.starttls()
   # Login to gmail account
   gmail.login(from_email, from_password)
   # Send mail
   gmail.send_message(msg)

de