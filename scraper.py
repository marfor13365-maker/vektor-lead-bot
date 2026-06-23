import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync  # ← добавь это

def human_delay(min_sec=8, max_sec=18):
    """Человеческие паузы"""
    time.sleep(random.uniform(min_sec, max_sec))

def scrape_yandex_maps(query: str, max_results: int = 15, max_pages: int = 2):
    leads = []
    print(f"🔍 Начинаем парсинг: {query}")
    
    with sync_playwright() as p:
        # Запуск браузера с защитой
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            locale='ru-RU'
        )
        
        # Применяем stealth
        stealth_sync(context)
        
        page = context.new_page()
        
        try:
            url = f"https://yandex.ru/maps/search/{query.replace(' ', '%20')}/"
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            human_delay(10, 16)
            
            for page_num in range(1, max_pages + 1):
                print(f"   Страница {page_num}/{max_pages}...")
                
                # Прокрутка страницы для подгрузки карточек
                for _ in range(3):
                    page.keyboard.press("PageDown")
                    human_delay(4, 8)
                
                # Актуальные селекторы Яндекса (на июнь 2026)
                cards = page.locator('div[data-testid="search-snippet"], div[class*="search-snippet"]').all()
                
                for card in cards[:max_results]:
                    try:
                        # Название компании
                        name_elem = card.locator('h1, [class*="title"], [class*="name"], [class*="business-card"]').first
                        name = name_elem.inner_text(timeout=5000).strip() if name_elem.count() > 0 else ""
                        
                        # Сайт
                        site = None
                        try:
                            link_elem = card.locator('a[href^="http"]').first
                            if link_elem.count() > 0:
                                site = link_elem.get_attribute('href')
                        except:
                            pass
                        
                        # Телефон
                        phone = None
                        try:
                            phone_elem = card.locator('span[class*="phone"], [class*="phone"], [class*="contact"]').first
                            if phone_elem.count() > 0:
                                phone = phone_elem.inner_text(timeout=3000).strip()
                        except:
                            pass
                        
                        if name and len(name) > 2:
                            leads.append({
                                "company": name,
                                "site": site,
                                "phone": phone,
                                "query": query
                            })
                    except:
                        continue
                
                # Длинная пауза между страницами
                if page_num < max_pages:
                    human_delay(25, 45)
                    
        except Exception as e:
            print(f"⚠️ Ошибка при парсинге {query}: {e}")
        finally:
            browser.close()
    
    print(f"✅ Собрано {len(leads)} лидов по запросу '{query}'")
    return leads[:max_results]
