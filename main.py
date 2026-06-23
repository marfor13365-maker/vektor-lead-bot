import time
import random
import traceback
import uvicorn
from fastapi import FastAPI, Response
from database import DB
from scraper import scrape_yandex_maps
from enricher import enrich_lead_with_email, generate_personalized_letter  # ← добавил enrich
from mailer import send_email

app = FastAPI()
db = DB()

# ==================== ОСНОВНЫЕ ЭНДПОИНТЫ ====================

@app.get("/")
def home():
    return {"status": "Lead Bot is running", "message": "Перейди на /run для запуска"}

@app.head("/")
def head_home():
    return Response(status_code=200)

@app.get("/run")
def run_bot():
    """Запускает парсинг + обогащение + рассылку (медленно и стабильно)"""
    print("🚀 Запуск Lead Bot...")
    
    try:
        queries = [
            "кафе Москва", 
            "автосервис Санкт-Петербург", 
            "медицинский центр Екатеринбург", 
            "салон красоты Казань",
            # Добавляй/убирай запросы по желанию
        ]

        total_saved = 0
        sent_count = 0

        print("📊 Начинаем сбор лидов...")
        for query in queries:
            print(f"🔍 Парсим: {query}")
            try:
                leads = scrape_yandex_maps(query, max_results=8, max_pages=2)  # уменьшил для стабильности
                
                for lead in leads:
                    try:
                        # === КРИТИЧНО: Обогащаем email ===
                        if not lead.get("email"):
                            enriched = enrich_lead_with_email(lead)  # ← новая функция
                            lead.update(enriched)
                        
                        if not lead.get("email"):
                            print(f"⚠️ Нет email у {lead['company']}, пропускаем")
                            continue
                        
                        # Сохраняем в базу
                        db.save_lead(
                            company=lead["company"],
                            site=lead.get("site"),
                            phone=lead.get("phone"),
                            email=lead.get("email")
                        )
                        print(f"💾 Сохранён: {lead['company']} → {lead.get('email')}")
                        total_saved += 1
                        
                    except Exception as e:
                        print(f"❌ Ошибка обработки лида {lead.get('company')}: {e}")
                    
                    time.sleep(random.uniform(8, 15))  # пауза между лидами
                    
            except Exception as e:
                print(f"❌ Ошибка парсинга {query}: {e}")
                continue
            
            time.sleep(random.uniform(40, 70))  # Длинная пауза между запросами

        print(f"📊 Всего сохранено лидов: {total_saved}")

        # === Рассылка (тоже медленно) ===
        print("📧 Начинаем рассылку...")
        new_leads = db.get_new_leads(limit=15)  # ограничили
        
        for lead in new_leads:
            if not lead.get("email"):
                continue
                
            try:
                print(f"✉️ Письмо для {lead['company']}")
                body = generate_personalized_letter(lead)
                subject = f"Предложение для {lead['company']}"
                
                send_email(lead["email"], subject, body, lead["company"])
                
                db.supabase.table("leads").update({"status": "sent"}).eq("id", lead["id"]).execute()
                sent_count += 1
                print(f"✅ Отправлено: {lead['company']}")
                
                time.sleep(random.uniform(18, 35))  # Важная пауза между письмами
                
            except Exception as e:
                print(f"❌ Ошибка отправки {lead.get('company')}: {e}")
                continue

        print(f"✅ Цикл завершён. Сохранено: {total_saved} | Отправлено: {sent_count}")
        return {
            "status": "success",
            "total_saved": total_saved,
            "sent": sent_count
        }

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {error_detail}")
        return {"status": "error", "detail": str(e)}


# ==================== ПРОВЕРОЧНЫЕ ЭНДПОИНТЫ ====================

@app.get("/check_scraper")
def check_scraper():
    """Тест парсера"""
    try:
        test_leads = scrape_yandex_maps("кафе Москва", max_results=5, max_pages=1)
        with_email = sum(1 for lead in test_leads if lead.get("email"))
        
        return {
            "status": "success",
            "found": len(test_leads),
            "with_email": with_email,
            "sample": test_leads[:2]
        }
    except Exception as e:
        return {"status": "error", "detail": str(e), "trace": traceback.format_exc()}


@app.get("/check_db")
def check_database():
    # ... (оставь как было, или могу улучшить)
    pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
