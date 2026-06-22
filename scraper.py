import time
import random
from playwright.sync_api import sync_playwright
from config import SUPABASE_URL  # только для теста, если нужно

def scrape_yandex_maps(query: str, max_results: int = 20):
    leads = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        page.goto(f"https://yandex.ru/maps/search/{query.replace(' ', '%20')}/", wait_until="domcontentloaded")
        time.sleep(6)
        
        for _ in range(4):   # несколько прокруток
            cards = page.locator('[data-testid="search-snippet"]').all() or page.locator('div[class*="search-snippet"]').all()
            
            for card in cards[:max_results]:
                try:
                    name = card.locator('h1, [class*="title"], [class*="name"]').first.inner_text(timeout=3000).strip()
                    link = card.locator('a[href^="http"]').first.get_attribute('href', timeout=3000)
                    phone = None
                    try:
                        phone_elem = card.locator('span[class*="phone"], [class*="phone"]').first
                        if phone_elem.count() > 0:
                            phone = phone_elem.inner_text(timeout=2000).strip()
                    except:
                        pass
                    
                    if name and len(name) > 2:
                        leads.append({
                            "company": name,
                            "site": link,
                            "phone": phone
                        })
                except:
                    continue
            
            page.keyboard.press("PageDown")
            time.sleep(random.uniform(7, 14))
        
        browser.close()
    return leads[:max_results]
