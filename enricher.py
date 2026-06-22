from grok import Grok   # или используй openai-compatible client
from config import GROK_API_KEY

client = Grok(api_key=GROK_API_KEY)

def generate_personalized_letter(lead):
    site_info = lead.get('site', 'не указан')
    prompt = f"""
Ты — менеджер студии Vektorizi. Напиши короткое, естественное и персонализированное письмо владельцу компании "{lead['company']}".
У них сайт: {site_info}.
Мы делаем Telegram-боты, современные сайты и автоматизацию бизнес-процессов, которые работают в России без VPN.
Предложи бесплатный аудит сайта/процессов (5-10 минут).
Тон: дружелюбный, экспертный, без навязчивости. Максимум 180 слов.
    """
    response = client.chat.completions.create(
        model="grok-beta",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400
    )
    return response.choices[0].message.content
