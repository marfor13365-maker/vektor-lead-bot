import time
import random
import traceback
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
    
    try:
        queries = [
            "кафе Москва", 
            "автосервис Санкт-Петербург", 
            "медицинский центр Екатеринбург", 
            "салон красоты Казань"
        ]

        # Сбор лидов
        print("📊 Начинаем сбор лидов...")
        for query in queries:
            print(f"🔍 Парсим: {query}")
            try:
                leads = scrape_yandex_maps(query, max_results=10)
                print(f"✅ Найдено {len(leads)} лидов для {query}")
                
                for lead in leads:
                    try:
                        db.save_lead(
                            company=lead["company"], 
                            site=lead.get("site"), 
                            phone=lead.get("phone")
                        )
                        print(f"💾 Сохранён лид: {lead['company']}")
                    except Exception as e:
                        print(f"❌ Ошибка сохранения лида {lead.get('company', 'unknown')}: {e}")
                    
                    time.sleep(random.uniform(10, 20))
                    
            except Exception as e:
                print(f"❌ Ошибка парсинга {query}: {e}")
                continue

        # Рассылка
        print("📧 Начинаем рассылку...")
        try:
            new_leads = db.get_new_leads(limit=20)
            print(f"📬 Найдено {len(new_leads)} новых лидов для рассылки")
            
            for lead in new_leads:
                if lead.get("email"):
                    try:
                        print(f"✉️ Генерируем письмо для {lead['company']}")
                        body = generate_personalized_letter(lead)
                        subject = f"Бесплатный аудит для {lead['company']}"
                        
                        print(f"📤 Отправляем письмо на {lead['email']}")
                        send_email(lead["email"], subject, body, lead["company"])
                        print(f"✅ Письмо отправлено для {lead['company']}")
                        
                        time.sleep(random.uniform(20, 35))
                        
                    except Exception as e:
                        print(f"❌ Ошибка при обработке {lead.get('company', 'unknown')}: {e}")
                        continue
                else:
                    print(f"⚠️ У лида {lead.get('company', 'unknown')} нет email")
                    
        except Exception as e:
            print(f"❌ Ошибка получения лидов из БД: {e}")
            return {"status": "error", "detail": f"Ошибка БД: {str(e)}"}

        print("✅ Цикл успешно выполнен!")
        return {"status": "success", "message": "Цикл выполнен"}

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {error_detail}")
        return {
            "status": "error", 
            "detail": str(e), 
            "trace": error_detail
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
