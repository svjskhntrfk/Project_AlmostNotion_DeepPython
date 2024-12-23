import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select
from src.db.cfg import settings
from src.db.models import Notification, Board, ToDoList, Task, User

def send_email_after_register(email, subject, message):
    try:
        # Создаем объект MIMEMultipart
        msg = MIMEMultipart()
        msg['From'] = settings.GMAIL_FROM
        msg['To'] = email
        msg['Subject'] = subject

        # Добавляем HTML-контент
        html_message = f"""
        <html>
            <body>
                <h1>Привет!</h1>
                <p>Ты успешно зарегистрировался в MindSpace.</p>
                <p>Теперь ты можешь начать использовать нашу платформу для управления задачами и проектами.</p>
                <p>Если у тебя возникнут вопросы или нужна помощь, обращайся к нам.</p>
                <p>Спасибо, что выбрал MindSpace!</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_message, 'html'))

        # Создаем SMTP-соединение
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Логинимся
        server.login(settings.GMAIL_FROM, settings.GMAIL_PASSWORD)
        
        # Отправляем письмо
        server.send_message(msg)
        
        # Закрываем соединение
        server.quit()
        
        return True
    except Exception as e:
        print(f"Ошибка при отправке email: {str(e)}")
        return False


def send_email_before_deadline(email, subject, message):
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.GMAIL_FROM
        msg['To'] = email
        msg['Subject'] = subject

        # Обновляем HTML-контент для уведомления о дедлайне
        html_message = f"""
        <html>
            <body>
                <h1>Уведомление о дедлайне!</h1>
                <p>{message}</p>
                <p>Пожалуйста, проверьте вашу задачу.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_message, 'html'))

        # Создаем SMTP-соединение
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Логинимся
        server.login(settings.GMAIL_FROM, settings.GMAIL_PASSWORD)
        
        # Отправляем письмо
        server.send_message(msg)
        
        # Закрываем соединение
        server.quit()
        
        return True
    except Exception as e:
        print(f"Ошибка при отправке email: {str(e)}")
        return False


async def check_and_send_notifications(session: AsyncSession):
    """
    Проверяет TodoLists с приближающимися дедлайнами и отправляет уведомления
    """
    try:
        # Получаем текущее время
        now = datetime.now()
        # Получаем время через 1 минуту
        deadline_before = now + timedelta(minutes=1)
        
        # Получаем все доски с их todo-листами, у которых скоро дедлайн
        query = (
            select(Board)
            .join(Board.todo_lists)
            .where(
                ToDoList.deadline <= deadline_before,
                ToDoList.deadline > now,  # только будущие дедлайны
            )
        )
        
        result = await session.execute(query)
        boards = result.unique().scalars().all()
        
        for board in boards:
            for todo_list in board.todo_lists:
                if todo_list.deadline and now < todo_list.deadline <= deadline_before:
                    # Получаем email владельца доски
                    owner = await session.get(User, board.user_id)
                    if owner:
                        subject = "Приближается дедлайн списка задач!"
                        message = f"Список задач '{todo_list.title}' должен быть выполнен через 1 минуту!"
                        send_email_before_deadline(owner.email, subject, message)
                        
                        # Отправляем уведомления всем участникам доски
                        for collaborator in board.collaborators:
                            if collaborator.id != owner.id:  # не отправляем повторно владельцу
                                send_email_before_deadline(collaborator.email, subject, message)
        
    except Exception as e:
        print(f"Ошибка при проверке и отправке уведомлений: {str(e)}")
