import time
import random
import uvicorn
from fastapi import FastAPI
from database import DB
from scraper import scrape_yandex_maps
from enricher import generate_personalized_letter
from mailer import send_email

app = FastAPI()
db = DB()

@app.get("/")
def home():
    return {"status": "Lead Bot is running", "message": "Перейди на /run для запуска"}

@app.get("/run")
def run_bot():
    print("🚀 Запуск Lead Bot...")
    queries = [
        "кафе Москва", "автосервис Санкт-Петербург", 
        "медицинский центр Екатеринбург", "салон красоты Казань"
    ]

    # Сбор лидов
    for query in queries:
        print(f"🔍 Парсим: {query}")
        leads = scrape_yandex_maps(query, max_results=10)
        for lead in leads:
            db.save_lead(company=lead["company"], site=lead.get("site"), phone=lead.get("phone"))
            time.sleep(random.uniform(10, 20))

    # Рассылка
    new_leads = db.get_new_leads(limit=20)
    for lead in new_leads:
        if lead.get("email"):
            try:
                body = generate_personalized_letter(lead)
                subject = f"Бесплатный аудит для {lead['company']}"
                send_email(lead["email"], subject, body, lead["company"])
                time.sleep(random.uniform(20, 35))
            except Exception as e:
                print(f"Ошибка при обработке {lead.get('company')}: {e}")

    return {"status": "success", "message": "Цикл выполнен"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
