import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL, EMAIL_PASSWORD

def send_email(to_email: str, subject: str, body: str, company: str):
    if not to_email or "@" not in to_email:
        print(f"Пропуск: нет корректного email для {company}")
        return False

    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg['Reply-To'] = EMAIL

    # Добавляем отписку (важно для безопасности)
    full_body = f"{body}\n\n---\nЕсли не хотите получать письма — ответьте 'отписаться'"

    msg.attach(MIMEText(full_body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # или smtp.yandex.ru
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ Отправлено: {company} → {to_email}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки {to_email}: {e}")
        return False
