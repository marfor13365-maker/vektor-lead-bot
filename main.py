import time
import random
import traceback
import uvicorn
from fastapi import FastAPI, Response
from database import DB
from scraper import scrape_yandex_maps
from enricher import generate_personalized_letter
from mailer import send_email

app = FastAPI()
db = DB()

# ==================== ОСНОВНЫЕ ЭНДПОИНТЫ ====================

@app.get("/")
def home():
    """Главная страница — проверка, что бот жив"""
    return {"status": "Lead Bot is running", "message": "Перейди на /run для запуска"}

@app.head("/")
def head_home():
    """Для UptimeRobot — HEAD-запросы без тела"""
    return Response(status_code=200)

@app.get("/run")
def run_bot():
    """Запускает парсинг и рассылку"""
    print("🚀 Запуск Lead Bot...")
    
    try:
        queries = [
            "кафе Москва", 
            "автосервис Санкт-Петербург", 
            "медицинский центр Екатеринбург", 
            "салон красоты Казань",
            "юридическая компания Москва",
            "IT компания Санкт-Петербург",
            "строительная компания Москва",
            "агентство недвижимости Казань"
        ]

        # Сбор лидов
        print("📊 Начинаем сбор лидов...")
        total_leads = 0
        for query in queries:
            print(f"🔍 Парсим: {query}")
            try:
                leads = scrape_yandex_maps(query, max_results=10)
                print(f"✅ Найдено {len(leads)} лидов для {query}")
                
                for lead in leads:
                    try:
                        # Проверяем, есть ли email
                        if not lead.get("email"):
                            print(f"⚠️ У {lead['company']} нет email, пропускаем")
                            continue
                            
                        db.save_lead(
                            company=lead["company"], 
                            site=lead.get("site"), 
                            phone=lead.get("phone"),
                            email=lead.get("email")
                        )
                        print(f"💾 Сохранён лид: {lead['company']} ({lead.get('email')})")
                        total_leads += 1
                    except Exception as e:
                        print(f"❌ Ошибка сохранения лида {lead.get('company', 'unknown')}: {e}")
                    
                    time.sleep(random.uniform(5, 10))
                    
            except Exception as e:
                print(f"❌ Ошибка парсинга {query}: {e}")
                continue

        print(f"📊 Всего сохранено лидов: {total_leads}")

        # Рассылка
        print("📧 Начинаем рассылку...")
        try:
            new_leads = db.get_new_leads(limit=20)
            print(f"📬 Найдено {len(new_leads)} новых лидов для рассылки")
            
            if len(new_leads) == 0:
                print("⚠️ Нет новых лидов для рассылки")
                return {"status": "success", "message": "Нет новых лидов для рассылки", "total_saved": total_leads}
            
            sent_count = 0
            for lead in new_leads:
                if lead.get("email"):
                    try:
                        print(f"✉️ Генерируем письмо для {lead['company']}")
                        body = generate_personalized_letter(lead)
                        subject = f"Бесплатный аудит для {lead['company']}"
                        
                        print(f"📤 Отправляем письмо на {lead['email']}")
                        send_email(lead["email"], subject, body, lead["company"])
                        print(f"✅ Письмо отправлено для {lead['company']}")
                        
                        # Обновляем статус лида
                        db.supabase.table("leads").update({"status": "sent"}).eq("id", lead["id"]).execute()
                        sent_count += 1
                        
                        time.sleep(random.uniform(15, 25))
                        
                    except Exception as e:
                        print(f"❌ Ошибка при обработке {lead.get('company', 'unknown')}: {e}")
                        continue
                else:
                    print(f"⚠️ У лида {lead.get('company', 'unknown')} нет email")
            
            print(f"✅ Отправлено писем: {sent_count}")
                    
        except Exception as e:
            print(f"❌ Ошибка получения лидов из БД: {e}")
            return {"status": "error", "detail": f"Ошибка БД: {str(e)}"}

        print("✅ Цикл успешно выполнен!")
        return {
            "status": "success", 
            "message": "Цикл выполнен", 
            "total_saved": total_leads,
            "sent": sent_count if 'sent_count' in locals() else 0
        }

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {error_detail}")
        return {
            "status": "error", 
            "detail": str(e), 
            "trace": error_detail
        }


# ==================== ЭНДПОИНТЫ ДЛЯ ПРОВЕРКИ ====================

@app.get("/check_db")
def check_database():
    """Проверяет, что собрано в базе данных"""
    try:
        response = db.supabase.table("leads").select("*").limit(100).execute()
        leads = response.data
        
        if not leads:
            return {
                "status": "empty",
                "message": "В базе данных нет записей",
                "total": 0
            }
        
        total = len(leads)
        with_email = sum(1 for lead in leads if lead.get("email"))
        with_phone = sum(1 for lead in leads if lead.get("phone"))
        with_site = sum(1 for lead in leads if lead.get("site"))
        sent = sum(1 for lead in leads if lead.get("status") == "sent")
        
        return {
            "status": "success",
            "total": total,
            "stats": {
                "with_email": with_email,
                "with_phone": with_phone,
                "with_site": with_site,
                "sent": sent,
                "new": total - sent
            },
            "sample": leads[:5]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "trace": traceback.format_exc()
        }


@app.get("/check_scraper")
def check_scraper():
    """Проверяет парсинг без сохранения в БД"""
    try:
        from scraper import scrape_yandex_maps
        test_leads = scrape_yandex_maps("кафе Москва", max_results=5)
        
        with_email = sum(1 for lead in test_leads if lead.get("email"))
        
        return {
            "status": "success",
            "found": len(test_leads),
            "with_email": with_email,
            "sample": test_leads[:3]
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "trace": traceback.format_exc()
        }


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
