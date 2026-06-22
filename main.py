import time
import random
from database import DB
from scraper import scrape_yandex_maps
from enricher import generate_personalized_letter
from mailer import send_email

db = DB()

def run_cycle():
    print("🚀 Запуск цикла сбора и рассылки...")

    # Ниши для старта (меняй и добавляй)
    queries = [
        "кафе Москва",
        "автосервис Санкт-Петербург",
        "медицинский центр Екатеринбург",
        "магазин одежды Новосибирск",
        "салон красоты Казань",
        # Добавляй свои ниши
    ]

    for query in queries:
        print(f"🔍 Парсим: {query}")
        leads = scrape_yandex_maps(query, max_results=15)
        
        for lead in leads:
            db.save_lead(
                company=lead["company"],
                site=lead.get("site"),
                phone=lead.get("phone")
            )
            time.sleep(random.uniform(12, 25))  # безопасность

    # Рассылка (только тем, у кого есть email)
    new_leads = db.get_new_leads(limit=30)
    print(f"Найдено новых лидов для рассылки: {len(new_leads)}")

    for lead in new_leads:
        if lead.get("email"):
            body = generate_personalized_letter(lead)
            subject = f"Как увеличить заявки для {lead['company']}?"
            
            send_email(
                to_email=lead["email"],
                subject=subject,
                body=body,
                company=lead["company"]
            )
            # Можно обновить статус в БД на "sent"
            time.sleep(random.uniform(20, 35))  # пауза между письмами

    print("✅ Цикл завершён")

if __name__ == "__main__":
    run_cycle()
