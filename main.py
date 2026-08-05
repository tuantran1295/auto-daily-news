#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import datetime
import re
import subprocess
import time
import requests
from bs4 import BeautifulSoup

# Header HTTP giả lập trình duyệt Chrome hiện đại
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
}

# Đường dẫn thư mục làm việc và file output
WORKSPACE_DIR = "/Users/remakit12/Desktop/Daily news app"
OUTPUT_HTML = os.path.join(WORKSPACE_DIR, "today_news.html")

# Tọa độ các thành phố lớn tại Việt Nam cho Open-Meteo API
CITIES = {
    "Hà Nội": {"lat": 21.0285, "lon": 105.8542},
    "Đà Nẵng": {"lat": 16.0544, "lon": 108.2022},
    "TP. Hồ Chí Minh": {"lat": 10.8231, "lon": 106.6297}
}

# Ánh xạ mã thời tiết WMO sang Tiếng Việt và Icon tương ứng
# Nguồn: WMO weather interpretation codes (https://open-meteo.com/en/docs)
WEATHER_CODES = {
    0: ("Trời quang, nắng ấm", "☀️", "clear-sky"),
    1: ("Ít mây, trời trong", "🌤️", "mainly-clear"),
    2: ("Mây rải rác", "⛅", "partly-cloudy"),
    3: ("Trời u ám, nhiều mây", "☁️", "overcast"),
    45: ("Có sương mù", "🌫️", "fog"),
    48: ("Sương mù đóng băng", "🌫️", "depositing-rime-fog"),
    51: ("Mưa phùn nhẹ", "🌧️", "drizzle-light"),
    53: ("Mưa phùn vừa", "🌧️", "drizzle-moderate"),
    55: ("Mưa phùn dày đặc", "🌧️", "drizzle-dense"),
    56: ("Mưa phùn lạnh nhẹ", "🌧️", "freezing-drizzle-light"),
    57: ("Mưa phùn lạnh đặc", "🌧️", "freezing-drizzle-dense"),
    61: ("Mưa rào nhẹ", "🌧️", "rain-slight"),
    63: ("Mưa vừa", "🌧️", "rain-moderate"),
    65: ("Mưa to", "🌧️", "rain-heavy"),
    66: ("Mưa lạnh nhẹ", "🌧️", "freezing-rain-light"),
    67: ("Mưa lạnh nặng", "🌧️", "freezing-rain-heavy"),
    71: ("Tuyết rơi nhẹ", "❄️", "snow-fall-slight"),
    73: ("Tuyết rơi vừa", "❄️", "snow-fall-moderate"),
    75: ("Tuyết rơi nặng", "❄️", "snow-fall-heavy"),
    77: ("Mưa đá nhỏ", "❄️", "snow-grains"),
    80: ("Mưa rào rải rác", "🌦️", "rain-showers-slight"),
    81: ("Mưa rào vừa", "🌧️", "rain-showers-moderate"),
    82: ("Mưa rào rất to", "⛈️", "rain-showers-violent"),
    85: ("Mưa tuyết nhẹ", "❄️", "snow-showers-light"),
    86: ("Mưa tuyết nặng", "❄️", "snow-showers-heavy"),
    95: ("Có dông bão", "⛈️", "thunderstorm"),
    96: ("Dông kèm mưa đá nhẹ", "⛈️", "thunderstorm-hail-slight"),
    99: ("Dông bão kèm mưa đá lớn", "🌪️", "thunderstorm-hail-heavy")
}

def get_weather_info(city_name, lat, lon):
    """
    Gọi Open-Meteo API để lấy thời tiết hiện tại của một thành phố (có cơ chế thử lại nếu lỗi)
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&timezone=Asia/Bangkok"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HTTP_HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            current = data.get("current", {})
            
            code = current.get("weather_code", 0)
            desc, emoji, weather_class = WEATHER_CODES.get(code, ("Thời tiết không xác định", "🌡️", "unknown"))
            
            return {
                "success": True,
                "city": city_name,
                "temp": current.get("temperature_2m", 0.0),
                "feel_temp": current.get("apparent_temperature", 0.0),
                "humidity": current.get("relative_humidity_2m", 0),
                "precipitation": current.get("precipitation", 0.0),
                "wind_speed": current.get("wind_speed_10m", 0.0),
                "weather_code": code,
                "description": desc,
                "emoji": emoji,
                "class": weather_class
            }
        except Exception as e:
            print(f"Lỗi khi lấy thời tiết cho {city_name} (Lần thử {attempt + 1}/{max_retries}): {e}", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(2)  # Đợi 2 giây trước khi thử lại
            else:
                return {
                    "success": False,
                    "city": city_name,
                    "error": str(e)
                }

def clean_html_tags(text):
    """Xóa các thẻ HTML thô khỏi văn bản mô tả"""
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

def parse_rss_feed(url, source_name):
    """
    Tải và parse RSS feed từ nguồn báo chí
    """
    items = []
    try:
        response = requests.get(url, headers=HTTP_HEADERS, timeout=10)
        response.raise_for_status()
        xml_data = response.content
        soup = BeautifulSoup(xml_data, 'xml')
        
        for item in soup.find_all('item'):
            title = item.find('title').text if item.find('title') else ""
            link = item.find('link').text if item.find('link') else ""
            desc_raw = item.find('description').text if item.find('description') else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') else ""
            
            desc = desc_raw
            img_url = ""
            img_match = re.search(r'src="([^"]+)"', desc_raw)
            if img_match:
                img_url = img_match.group(1)
            
            desc = clean_html_tags(desc_raw)
            
            items.append({
                "title": title.strip(),
                "link": link.strip(),
                "description": desc,
                "image": img_url,
                "pub_date": pub_date.strip(),
                "source": source_name
            })
    except Exception as e:
        print(f"Lỗi khi parse RSS từ {source_name} ({url}): {e}", file=sys.stderr)
    return items

def scrape_nchmf_warnings():
    """
    Cào trực tiếp tin tức cảnh báo thiên tai từ trang web của Trung tâm Khí tượng Thủy văn Quốc gia (NCHMF)
    """
    warnings = []
    url = "https://nchmf.gov.vn/"
    try:
        response = requests.get(url, headers=HTTP_HEADERS, timeout=15)
        response.raise_for_status()
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
            
        articles = soup.find_all('div', class_='news-item') or soup.find_all('div', class_='row')
        
        for article in articles:
            link_tag = article.find('a')
            if not link_tag or not link_tag.get('href'):
                continue
            
            title_tag = article.find('h4') or article.find('a', class_='title') or link_tag
            title = title_tag.text.strip()
            
            href = link_tag.get('href')
            if not href.startswith('http'):
                href = "https://nchmf.gov.vn" + href
                
                desc_tag = article.find('p', class_='summary') or article.find('p')
                desc = desc_tag.text.strip() if desc_tag else ""
                
                if title and (any(kw in title.lower() for kw in ["bão", "áp thấp", "mưa lớn", "lũ", "nắng nóng", "dự báo", "cảnh báo"])):
                    warnings.append({
                        "title": title,
                        "link": href,
                        "description": desc,
                        "source": "NCHMF",
                        "pub_date": datetime.datetime.now().strftime("%d/%m/%Y")
                    })
            
            # Nếu không tìm thấy class cụ thể, quét tất cả link của trang web để tìm tin cảnh báo
            if not warnings:
                links = soup.find_all('a')
                for link in links:
                    text = link.text.strip()
                    href = link.get('href', '')
                    if len(text) > 15 and any(kw in text.lower() for kw in ["bão", "áp thấp", "mưa lớn", "lũ", "sạt lở", "triều cường", "khẩn cấp"]):
                        if not href.startswith('http'):
                            href = "https://nchmf.gov.vn" + href
                        warnings.append({
                            "title": text,
                            "link": href,
                            "description": "Nhấn vào link để xem thông tin chi tiết trên website NCHMF.",
                            "source": "NCHMF (Cảnh báo)",
                            "pub_date": datetime.datetime.now().strftime("%d/%m/%Y")
                        })
    except Exception as e:
        print(f"Lỗi khi cào trang web NCHMF: {e}", file=sys.stderr)
    return warnings

def process_news_and_warnings():
    """
    Tổng hợp và lọc tin tức theo các chuyên mục: Bão/Thiên tai, Thời tiết thông thường, Công nghệ (GenK), AI, Giới trẻ, World Cup và GameK (Game/Esports).
    Đặc biệt: Ưu tiên lọc tin bài chủ đề AI từ TẤT CẢ các nguồn báo chí (Global AI Filter).
    """
    weather_feeds = [
        ("https://vnexpress.net/rss/thoi-su.rss", "VnExpress Thời sự"),
        ("https://tuoitre.vn/rss/thoi-su.rss", "Tuổi Trẻ Thời sự")
    ]
    tech_feeds = [
        ("https://genk.vn/rss/home.rss", "GenK Trang chủ"),
        ("https://genk.vn/rss/ai.rss", "GenK AI"),
        ("https://vnexpress.net/rss/so-hoa.rss", "VnExpress Số hóa")
    ]
    youth_feeds = [
        ("https://thanhnien.vn/rss/gioi-tre.rss", "Thanh Niên Giới trẻ")
    ]
    sports_feeds = [
        ("https://vnexpress.net/rss/the-thao.rss", "VnExpress Thể thao"),
        ("https://tuoitre.vn/rss/the-thao.rss", "Tuổi Trẻ Thể thao")
    ]
    game_feeds = [
        ("https://gamek.vn/trang-chu.rss", "GameK Trang chủ"),
        ("https://gamek.vn/esport.rss", "GameK Esports")
    ]
    
    # 1. Cào dữ liệu từ tất cả các nhóm RSS
    weather_items = []
    for url, source in weather_feeds:
        weather_items.extend(parse_rss_feed(url, source))
        
    # Lấy thêm tin từ NCHMF
    nchmf_warnings = scrape_nchmf_warnings()
    weather_items.extend(nchmf_warnings)
    
    tech_items = []
    for url, source in tech_feeds:
        tech_items.extend(parse_rss_feed(url, source))
        
    youth_items = []
    for url, source in youth_feeds:
        youth_items.extend(parse_rss_feed(url, source))
        
    sports_items = []
    for url, source in sports_feeds:
        sports_items.extend(parse_rss_feed(url, source))
        
    game_items = []
    for url, source in game_feeds:
        game_items.extend(parse_rss_feed(url, source))
        
    # Từ khóa lọc bão & thiên tai
    priority_keywords = ["bão", "áp thấp", "lũ quét", "sạt lở", "triều cường", "mưa lớn", "ngập lụt", "lốc xoáy", "thiên tai", "lũ lụt"]
    weather_keywords = ["thời tiết", "nắng nóng", "mưa giông", "gió giật", "không khí lạnh", "dự báo", "triều cường"]
    
    # Từ khóa lọc tin AI mở rộng
    ai_keywords = [
        "ai", "trí tuệ nhân tạo", "chatgpt", "gemini", "copilot", "openai", "nvidia", 
        "llm", "học máy", "machine learning", "deep learning", "claude", "midjourney", 
        "sora", "grok", "deepseek", "generative ai", "ai tạo sinh", "robot ai", 
        "mô hình ngôn ngữ", "tự động hóa ai", "sam altman", "jensen huang", "agentic ai"
    ]
    
    # Từ khóa lọc tin World Cup 2026
    wc_keywords = [
        "world cup", "worldcup", "wc 2026", "wc2026", "fifa", "bóng đá", 
        "bán kết", "chung kết", "trận đấu", "tuyển quốc gia", "đội tuyển", 
        "cầu thủ", "cup thế giới", "lịch thi đấu", "vô địch"
    ]
    
    priority_news = []
    normal_weather_news = []
    tech_news = []
    ai_news = []
    youth_news = []
    wc_news = []
    game_news = []
    
    seen_titles = set()
    
    # --- BƯỚC QUAN TRỌNG: THUẬT TOÁN ĐỌC & QUÉT AI TOÀN CỤC (GLOBAL AI FILTER) ---
    # Quét trước tất cả tin từ mọi nguồn (GenK, GameK, VnExpress, Tuổi Trẻ, Thanh Niên...) để ưu tiên bài về AI
    all_raw_items = [("weather", item) for item in weather_items] + \
                    [("tech", item) for item in tech_items] + \
                    [("youth", item) for item in youth_items] + \
                    [("sports", item) for item in sports_items] + \
                    [("game", item) for item in game_items]
                    
    non_ai_items = []
    for category, item in all_raw_items:
        title_lower = item["title"].lower()
        desc_lower = item["description"].lower() if item["description"] else ""
        
        clean_title = re.sub(r'[^\w\s]', '', title_lower).strip()
        if clean_title in seen_titles:
            continue
            
        # Kiểm tra xem bài viết từ BẤT KỲ NGUỒN NÀO có phải về AI không
        is_ai = any(kw in title_lower or kw in desc_lower for kw in ai_keywords if kw != "ai")
        if not is_ai:
            is_ai = bool(re.search(r'\b(ai)\b', title_lower)) or bool(re.search(r'\b(ai)\b', desc_lower))
            
        if is_ai:
            seen_titles.add(clean_title)
            ai_news.append(item)
        else:
            non_ai_items.append((category, item))

    # --- BƯỚC KẾ TIẾP: Phân loại các tin còn lại không thuộc AI ---
    for category, item in non_ai_items:
        title_lower = item["title"].lower()
        desc_lower = item["description"].lower() if item["description"] else ""
        
        clean_title = re.sub(r'[^\w\s]', '', title_lower).strip()
        if clean_title in seen_titles:
            continue
        seen_titles.add(clean_title)
        
        if category == "weather":
            is_priority = any(kw in title_lower or kw in desc_lower for kw in priority_keywords)
            is_weather = any(kw in title_lower or kw in desc_lower for kw in weather_keywords)
            if is_priority:
                priority_news.append(item)
            elif is_weather:
                normal_weather_news.append(item)
        elif category == "tech":
            tech_news.append(item)
        elif category == "youth":
            youth_news.append(item)
        elif category == "sports":
            is_wc = any(kw in title_lower or kw in desc_lower for kw in wc_keywords)
            if is_wc:
                wc_news.append(item)
        elif category == "game":
            game_news.append(item)
        
    return priority_news, normal_weather_news, tech_news, ai_news, youth_news, wc_news, game_news

def build_html_report(weather_data, priority_news, weather_news, tech_news, ai_news, youth_news, wc_news, game_news):
    """
    Tạo báo cáo HTML dạng Dashboard 3 cột đẹp mắt dựa trên dữ liệu thời tiết và tin tức đã thu thập
    """
    now = datetime.datetime.now()
    days_vi = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"]
    day_idx = (now.weekday() + 1) % 7
    date_str = f"{days_vi[day_idx]}, ngày {now.day:02d} tháng {now.month:02d} năm {now.year}"
    time_str = now.strftime("%H:%M")
    
    # --- 1. Tạo HTML cho cột Thời tiết ---
    weather_cards_html = ""
    for city, data in weather_data.items():
        if not data.get("success"):
            weather_cards_html += f"""
            <div class="weather-card error-card">
                <h3>{city}</h3>
                <p class="error-msg">Không thể tải thông tin thời tiết: {data.get('error', 'Lỗi không xác định')}</p>
            </div>
            """
            continue
            
        weather_cards_html += f"""
        <div class="weather-card {data['class']}">
            <div class="card-header">
                <h3>{data['city']}</h3>
                <span class="weather-emoji">{data['emoji']}</span>
            </div>
            <div class="temp-container">
                <span class="temp-val">{data['temp']}°C</span>
                <span class="weather-desc">{data['description']}</span>
            </div>
            <div class="weather-details">
                <div class="detail-item">
                    <span class="detail-label">Cảm giác:</span>
                    <span class="detail-val">{data['feel_temp']}°C</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Độ ẩm:</span>
                    <span class="detail-val">{data['humidity']}%</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Gió:</span>
                    <span class="detail-val">{data['wind_speed']} km/h</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Lượng mưa:</span>
                    <span class="detail-val">{data['precipitation']} mm</span>
                </div>
            </div>
        </div>
        """
        
    # --- 2. Tạo HTML cho cột Cảnh báo bão & thiên tai ---
    warning_section_html = ""
    if priority_news:
        warning_items_html = ""
        for item in priority_news[:4]: # Giới hạn tối đa 4 tin khẩn cấp
            img_html = f'<img src="{item["image"]}" alt="tin-anh" class="news-img">' if item.get("image") else ''
            warning_items_html += f"""
            <div class="news-item priority-item">
                {img_html}
                <div class="news-content">
                    <span class="badge badge-danger">{item['source']} - CẢNH BÁO BÃO</span>
                    <h4 class="news-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h4>
                    <p class="news-desc">{item['description']}</p>
                    <span class="news-date">📅 {item['pub_date']}</span>
                </div>
            </div>
            """
        warning_section_html = f"""
        <div class="section-box warning-box-active">
            <h2 class="section-title warning-title">🚨 CẢNH BÁO THIÊN TAI & BÃO ({len(priority_news)})</h2>
            <div class="news-list">
                {warning_items_html}
            </div>
        </div>
        """
    else:
        warning_section_html = """
        <div class="section-box warning-box-empty">
            <div class="no-warning-box">
                <span class="shield-icon">🛡️</span>
                <h3>Thời tiết thiên tai ổn định</h3>
                <p>Hiện không phát hiện cảnh báo thiên tai khẩn cấp nào tại Việt Nam.</p>
            </div>
        </div>
        """

    # --- 3. Tạo HTML cho các tin tức thời tiết phụ ---
    weather_news_html = ""
    if weather_news:
        for item in weather_news[:3]: # Lấy 3 tin thời tiết thường
            weather_news_html += f"""
            <div class="sub-news-card">
                <span class="badge badge-weather">{item['source']}</span>
                <h4 class="sub-news-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h4>
                <span class="news-date">📅 {item['pub_date']}</span>
            </div>
            """
    else:
        weather_news_html = "<p class='no-news'>Không có tin tức thời tiết phụ khác.</p>"

    # --- 4. Tạo HTML cho cột AI (Trí tuệ nhân tạo) ---
    ai_news_html = ""
    if ai_news:
        for item in ai_news[:8]: # Tối đa 8 tin AI nổi bật
            img_html = f'<img src="{item["image"]}" alt="tin-anh" class="news-img-small">' if item.get("image") else ''
            ai_news_html += f"""
            <div class="news-card ai-card">
                {img_html}
                <div class="news-card-body">
                    <span class="badge badge-ai">{item['source']} - Trí tuệ nhân tạo</span>
                    <h4 class="news-card-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h4>
                    <p class="news-card-desc">{item['description']}</p>
                    <span class="news-date">📅 {item['pub_date']}</span>
                </div>
            </div>
            """
    else:
        ai_news_html = "<p class='no-news'>Không tìm thấy cập nhật tin tức mới về AI.</p>"

    # --- 5. Tạo HTML cho cột Công nghệ (GenK) ---
    tech_news_html = ""
    if tech_news:
        for item in tech_news[:5]: # Tối đa 5 tin công nghệ GenK/VnExpress
            img_html = f'<img src="{item["image"]}" alt="tin-anh" class="news-img-small">' if item.get("image") else ''
            tech_news_html += f"""
            <div class="news-card tech-card">
                {img_html}
                <div class="news-card-body">
                    <span class="badge badge-tech">{item['source']}</span>
                    <h4 class="news-card-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h4>
                    <p class="news-card-desc">{item['description']}</p>
                    <span class="news-date">📅 {item['pub_date']}</span>
                </div>
            </div>
            """
    else:
        tech_news_html = "<p class='no-news'>Không có tin công nghệ mới.</p>"

    # --- 6. Tạo HTML cho cột Giới trẻ ---
    youth_news_html = ""
    if youth_news:
        for item in youth_news[:4]: # Giới hạn 4 tin giới trẻ
            img_html = f'<img src="{item["image"]}" alt="tin-anh" class="news-img-small">' if item.get("image") else ''
            youth_news_html += f"""
            <div class="news-card youth-card">
                {img_html}
                <div class="news-card-body">
                    <span class="badge badge-youth">{item['source']}</span>
                    <h4 class="news-card-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h4>
                    <p class="news-card-desc">{item['description']}</p>
                    <span class="news-date">📅 {item['pub_date']}</span>
                </div>
            </div>
            """
    else:
        youth_news_html = "<p class='no-news'>Không có tin tức giới trẻ mới.</p>"

    # --- 7. Tạo HTML cho cột World Cup ---
    wc_news_html = ""
    if wc_news:
        for item in wc_news[:4]: # Tối đa 4 tin World Cup
            img_html = f'<img src="{item["image"]}" alt="tin-anh" class="news-img-small">' if item.get("image") else ''
            wc_news_html += f"""
            <div class="news-card wc-card">
                {img_html}
                <div class="news-card-body">
                    <span class="badge badge-wc">{item['source']} - World Cup 2026</span>
                    <h4 class="news-card-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h4>
                    <p class="news-card-desc">{item['description']}</p>
                    <span class="news-date">📅 {item['pub_date']}</span>
                </div>
            </div>
            """
    else:
        wc_news_html = "<p class='no-news'>Hiện chưa cập nhật tin tức World Cup mới.</p>"

    # --- 8. Tạo HTML cho cột Game & Esports (GameK) ---
    game_news_html = ""
    if game_news:
        for item in game_news[:5]: # Tối đa 5 tin GameK
            img_html = f'<img src="{item["image"]}" alt="tin-anh" class="news-img-small">' if item.get("image") else ''
            game_news_html += f"""
            <div class="news-card game-card">
                {img_html}
                <div class="news-card-body">
                    <span class="badge badge-game">{item['source']}</span>
                    <h4 class="news-card-title"><a href="{item['link']}" target="_blank">{item['title']}</a></h4>
                    <p class="news-card-desc">{item['description']}</p>
                    <span class="news-date">📅 {item['pub_date']}</span>
                </div>
            </div>
            """
    else:
        game_news_html = "<p class='no-news'>Không có tin tức Game/Esports mới.</p>"

    # Toàn bộ Template HTML/CSS phong cách Premium Dashboard 3 cột
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bản tin Tổng hợp Sáng: Thời tiết, Công nghệ & AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient: linear-gradient(135deg, #090d16 0%, #0f1026 50%, #05060d 100%);
            --card-bg: rgba(17, 24, 39, 0.45);
            --card-border: rgba(255, 255, 255, 0.06);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            
            /* Theme color variables */
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.15);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.2);
            --success: #10b981;
            --warning: #f59e0b;
            
            --ai-purple: #8b5cf6;
            --ai-glow: rgba(139, 92, 246, 0.12);
            --tech-cyan: #06b6d4;
            --tech-glow: rgba(6, 182, 212, 0.12);
            --youth-pink: #ec4899;
            --youth-glow: rgba(236, 72, 153, 0.12);
            
            --wc-gold: #eab308;
            --wc-glow: rgba(234, 179, 8, 0.12);
            
            --game-green: #10b981;
            --game-glow: rgba(16, 185, 129, 0.12);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2rem 1.5rem;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}

        h1, h2, h3, h4 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        /* Header */
        header {{
            text-align: center;
            margin-bottom: 2.5rem;
            position: relative;
        }}

        header::after {{
            content: '';
            display: block;
            width: 120px;
            height: 4px;
            background: linear-gradient(90deg, var(--danger), var(--ai-purple), var(--tech-cyan));
            margin: 1.25rem auto 0;
            border-radius: 2px;
        }}

        .header-title {{
            font-size: 2.3rem;
            font-weight: 700;
            background: linear-gradient(to right, #ffffff, #c7d2fe, #f5d0fe, #a5f3fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.4rem;
        }}

        .header-meta {{
            font-size: 1.05rem;
            color: var(--text-muted);
            font-weight: 300;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }}

        .header-time {{
            background: rgba(99, 102, 241, 0.12);
            padding: 0.2rem 0.65rem;
            border-radius: 20px;
            color: #a5b4fc;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid rgba(99, 102, 241, 0.18);
        }}

        /* Dashboard Grid Layout (3 Columns) */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1.25fr 1fr;
            gap: 2rem;
            align-items: start;
        }}

        @media (max-width: 1100px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}

        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            body {{
                padding: 1.5rem 1rem;
            }}
            .header-title {{
                font-size: 1.8rem;
            }}
        }}

        /* Column Styles */
        .dashboard-col {{
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }}

        .col-title-bar {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-size: 1.3rem;
            font-weight: 700;
            border-bottom: 2px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 0.5rem;
            margin-bottom: 0.75rem;
            font-family: 'Outfit', sans-serif;
            letter-spacing: 0.02em;
        }}

        .col-weather-title {{ color: #a5f3fc; border-color: rgba(6, 182, 212, 0.15); }}
        .col-tech-title {{ color: #c7d2fe; border-color: rgba(139, 92, 246, 0.15); }}
        .col-youth-title {{ color: #fbcfe8; border-color: rgba(236, 72, 153, 0.15); }}
        .col-wc-title {{ color: #fef08a; border-color: rgba(234, 179, 8, 0.15); }}
        .col-game-title {{ color: #6ee7b7; border-color: rgba(16, 185, 129, 0.15); }}

        /* Section Container Box */
        .section-box {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 1.5rem;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            position: relative;
            overflow: hidden;
        }}

        /* --- Weather Section --- */
        .weather-list {{
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}

        .weather-card {{
            background: rgba(30, 41, 59, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 18px;
            padding: 1.25rem;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }}

        .weather-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary);
        }}

        .weather-card.clear-sky::before {{ background: var(--warning); }}
        .weather-card.mainly-clear::before,
        .weather-card.partly-cloudy::before {{ background: #3b82f6; }}
        .weather-card.overcast::before {{ background: #6b7280; }}
        .weather-card.rain-slight::before,
        .weather-card.rain-moderate::before,
        .weather-card.rain-showers-slight::before,
        .weather-card.rain-showers-moderate::before {{ background: var(--tech-cyan); }}
        .weather-card.rain-heavy::before,
        .weather-card.rain-showers-violent::before,
        .weather-card.thunderstorm::before {{ background: var(--danger); }}

        .weather-card:hover {{
            transform: translateY(-3px);
            border-color: rgba(255, 255, 255, 0.1);
            background: rgba(30, 41, 59, 0.5);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }}

        .weather-card.error-card {{
            border: 1px solid rgba(239, 68, 68, 0.2);
            background: rgba(239, 68, 68, 0.03);
        }}
        .weather-card.error-card::before {{
            background: var(--danger);
        }}
        .error-msg {{
            color: #fca5a5;
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}

        .card-header h3 {{
            font-size: 1.15rem;
            color: #ffffff;
            font-weight: 500;
        }}

        .weather-emoji {{
            font-size: 1.75rem;
        }}

        .temp-container {{
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}

        .temp-val {{
            font-size: 2.2rem;
            font-weight: 700;
            color: #ffffff;
            font-family: 'Outfit', sans-serif;
        }}

        .weather-desc {{
            font-size: 0.9rem;
            color: #cbd5e1;
            font-weight: 500;
        }}

        .weather-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 1rem;
        }}

        .detail-item {{
            display: flex;
            flex-direction: column;
        }}

        .detail-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .detail-val {{
            font-size: 0.85rem;
            font-weight: 600;
            color: #e2e8f0;
        }}

        /* --- Warning & Bão Section --- */
        .warning-box-active {{
            background: rgba(239, 68, 68, 0.04);
            border: 1px solid rgba(239, 68, 68, 0.15);
            animation: pulse-border 3s infinite alternate;
        }}

        @keyframes pulse-border {{
            0% {{ border-color: rgba(239, 68, 68, 0.15); }}
            100% {{ border-color: rgba(239, 68, 68, 0.35); }}
        }}

        .warning-title {{
            color: #fca5a5;
        }}

        .no-warning-box {{
            text-align: center;
            padding: 1rem 0;
        }}

        .shield-icon {{
            font-size: 2.2rem;
            display: block;
            margin-bottom: 0.5rem;
        }}

        .no-warning-box h3 {{
            color: var(--success);
            font-size: 1.1rem;
            margin-bottom: 0.25rem;
        }}

        .no-warning-box p {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        .news-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .news-item {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 14px;
            padding: 1rem;
            display: flex;
            gap: 1rem;
            transition: all 0.3s ease;
            position: relative;
        }}

        .news-item.priority-item::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background: var(--danger);
            border-radius: 3px 0 0 3px;
        }}

        .news-item:hover {{
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.08);
            transform: translateX(2px);
        }}

        .news-img {{
            width: 90px;
            height: 70px;
            object-fit: cover;
            border-radius: 8px;
            flex-shrink: 0;
        }}

        .news-content {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .badge {{
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            display: inline-block;
            width: fit-content;
            margin-bottom: 0.25rem;
        }}

        .badge-danger {{ background: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.25); }}
        .badge-weather {{ background: rgba(6, 182, 212, 0.12); color: #a5f3fc; border: 1px solid rgba(6, 182, 212, 0.2); }}
        .badge-ai {{ background: rgba(139, 92, 246, 0.15); color: #ddd6fe; border: 1px solid rgba(139, 92, 246, 0.25); }}
        .badge-tech {{ background: rgba(59, 130, 246, 0.12); color: #bfdbfe; border: 1px solid rgba(59, 130, 246, 0.2); }}
        .badge-youth {{ background: rgba(236, 72, 153, 0.12); color: #fbcfe8; border: 1px solid rgba(236, 72, 153, 0.2); }}
        .badge-wc {{ background: rgba(234, 179, 8, 0.15); color: #fef08a; border: 1px solid rgba(234, 179, 8, 0.25); }}
        .badge-game {{ background: rgba(16, 185, 129, 0.15); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.25); }}

        .news-title a {{
            color: #ffffff;
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
            transition: color 0.2s ease;
        }}

        .news-title a:hover {{
            color: #fca5a5;
            text-decoration: underline;
        }}

        .news-desc {{
            color: var(--text-muted);
            font-size: 0.8rem;
            margin: 0.25rem 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .news-date {{
            font-size: 0.7rem;
            color: #6b7280;
        }}

        /* --- Sub news card --- */
        .sub-news-card {{
            padding: 0.85rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        }}

        .sub-news-card:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}

        .sub-news-title a {{
            color: #cbd5e1;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            line-height: 1.4;
            transition: color 0.2s ease;
            display: block;
            margin-top: 0.25rem;
            margin-bottom: 0.2rem;
        }}

        .sub-news-title a:hover {{
            color: var(--primary);
        }}

        /* --- Tech & AI Grid Column --- */
        .news-card-grid {{
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}

        .news-card {{
            background: rgba(30, 41, 59, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 16px;
            overflow: hidden;
            display: flex;
            transition: all 0.3s ease;
        }}

        .news-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(255, 255, 255, 0.08);
            background: rgba(30, 41, 59, 0.4);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        }}

        .ai-card {{
            border-left: 3px solid var(--ai-purple);
            background: linear-gradient(90deg, var(--ai-glow) 0%, rgba(30, 41, 59, 0.2) 100%);
        }}

        .tech-card {{
            border-left: 3px solid var(--tech-cyan);
            background: linear-gradient(90deg, var(--tech-glow) 0%, rgba(30, 41, 59, 0.2) 100%);
        }}

        .youth-card {{
            border-left: 3px solid var(--youth-pink);
            background: linear-gradient(90deg, var(--youth-glow) 0%, rgba(30, 41, 59, 0.2) 100%);
        }}

        .wc-card {{
            border-left: 3px solid var(--wc-gold);
            background: linear-gradient(90deg, var(--wc-glow) 0%, rgba(30, 41, 59, 0.2) 100%);
        }}

        .game-card {{
            border-left: 3px solid var(--game-green);
            background: linear-gradient(90deg, var(--game-glow) 0%, rgba(30, 41, 59, 0.2) 100%);
        }}

        .news-img-small {{
            width: 110px;
            height: 90px;
            object-fit: cover;
            flex-shrink: 0;
            border-right: 1px solid rgba(255, 255, 255, 0.04);
        }}

        .news-card-body {{
            padding: 1rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            width: 100%;
        }}

        .news-card-title a {{
            color: #ffffff;
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 600;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            transition: color 0.2s ease;
        }}

        .ai-card .news-card-title a:hover {{ color: var(--ai-purple); }}
        .tech-card .news-card-title a:hover {{ color: var(--tech-cyan); }}
        .youth-card .news-card-title a:hover {{ color: var(--youth-pink); }}
        .wc-card .news-card-title a:hover {{ color: var(--wc-gold); }}
        .game-card .news-card-title a:hover {{ color: var(--game-green); }}

        .news-card-desc {{
            color: var(--text-muted);
            font-size: 0.8rem;
            margin: 0.35rem 0 0.5rem;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            line-height: 1.4;
        }}

        .no-news {{
            color: var(--text-muted);
            font-size: 0.85rem;
            text-align: center;
            padding: 1rem 0;
            font-style: italic;
        }}

        .footer {{
            text-align: center;
            margin-top: 4rem;
            color: #6b7280;
            font-size: 0.8rem;
            border-top: 1px solid rgba(255, 255, 255, 0.04);
            padding-top: 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <h1 class="header-title">Bản tin Sáng Đa chuyên mục</h1>
            <div class="header-meta">
                <span>{date_str}</span>
                <span class="header-time">🕒 Cập nhật: {time_str}</span>
            </div>
        </header>

        <!-- Dashboard Grid (3 Columns) -->
        <div class="dashboard-grid">
            
            <!-- CỘT 1: THỜI TIẾT & THIÊN TAI -->
            <div class="dashboard-col col-left">
                <div>
                    <div class="col-title-bar col-weather-title">🌤️ Thời tiết 3 Miền</div>
                    <div class="weather-list">
                        {weather_cards_html}
                    </div>
                </div>

                <!-- Cảnh báo thiên tai khẩn cấp -->
                {warning_section_html}

                <!-- Tin tức thời tiết phụ -->
                <div class="section-box">
                    <div class="col-title-bar col-weather-title" style="border:none; margin:0; padding:0; font-size:1.1rem;">🌊 Bản tin Môi trường & Thời tiết</div>
                    <div style="margin-top:0.75rem;">
                        {weather_news_html}
                    </div>
                </div>
            </div>

            <!-- CỘT 2: TRÍ TUỆ NHÂN TẠO (AI) & CÔNG NGHỆ -->
            <div class="dashboard-col col-center">
                <!-- Chuyên mục AI nổi bật -->
                <div>
                    <div class="col-title-bar col-tech-title">🧠 Trí tuệ Nhân tạo (AI)</div>
                    <div class="news-card-grid">
                        {ai_news_html}
                    </div>
                </div>

                <!-- Chuyên mục Thế giới công nghệ -->
                <div>
                    <div class="col-title-bar col-tech-title" style="color: #a5f3fc;">💻 Thế giới Công nghệ</div>
                    <div class="news-card-grid">
                        {tech_news_html}
                    </div>
                </div>
            </div>

            <!-- CỘT 3: WORLD CUP, GAMEK & GIỚI TRẺ -->
            <div class="dashboard-col col-right">
                <!-- Chuyên mục World Cup -->
                <div>
                    <div class="col-title-bar col-wc-title">🏆 FIFA World Cup 2026</div>
                    <div class="news-card-grid">
                        {wc_news_html}
                    </div>
                </div>

                <!-- Chuyên mục GameK -->
                <div>
                    <div class="col-title-bar col-game-title">🎮 Thế giới Game & Esports (GameK)</div>
                    <div class="news-card-grid">
                        {game_news_html}
                    </div>
                </div>

                <!-- Nhịp sống Giới trẻ -->
                <div>
                    <div class="col-title-bar col-youth-title">✨ Nhịp sống Giới trẻ</div>
                    <div class="news-card-grid">
                        {youth_news_html}
                    </div>
                </div>
            </div>

        </div>

        <!-- Footer -->
        <footer class="footer">
            <p>Phần mềm tự động cập nhật thời tiết và tin tức hàng ngày trên macOS.</p>
            <p>Nguồn dữ liệu: Open-Meteo API, VnExpress, Tuổi Trẻ, GenK, GameK, Thanh Niên. Hoàn thành tổng hợp lúc {time_str}.</p>
        </footer>
    </div>
</body>
</html>
"""
    # Ghi đè file html
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Đã xuất bản tin HTML thành công tại {OUTPUT_HTML}")

def send_macos_notification(weather_data, has_warnings):
    """
    Gửi notification cho macOS bằng cách chạy AppleScript qua osascript.
    Khi người dùng bấm vào thông báo hoặc sau đó, bản tin HTML sẽ được hiển thị.
    """
    # Tạo nội dung tóm tắt thời tiết
    hn = weather_data.get("Hà Nội", {})
    dn = weather_data.get("Đà Nẵng", {})
    hcm = weather_data.get("TP. Hồ Chí Minh", {})
    
    summary = ""
    if hn.get("success"):
        summary += f"HN: {hn['temp']}°C {hn['emoji']} | "
    if dn.get("success"):
        summary += f"ĐN: {dn['temp']}°C {dn['emoji']} | "
    if hcm.get("success"):
        summary += f"HCM: {hcm['temp']}°C {hcm['emoji']}"
        
    title = "Bản tin Thời tiết Sáng 8h"
    if has_warnings:
        title = "🚨 CẢNH BÁO BÃO & THIÊN TAI KHẨN CẤP!"
        subtitle = "Có tin bão/thiên tai mới tại Việt Nam"
    else:
        subtitle = "Thời tiết 3 miền ổn định"
        
    # Tạo mã AppleScript
    # display notification cần title, subtitle, và sound name (mặc định)
    sound_effect = "Basso" if has_warnings else "Ping"
    
    # Thoát các dấu nháy kép cho AppleScript
    title_escaped = title.replace('"', '\\"')
    subtitle_escaped = subtitle.replace('"', '\\"')
    summary_escaped = summary.replace('"', '\\"')
    
    applescript_cmd = f'display notification "{summary_escaped}" with title "{title_escaped}" subtitle "{subtitle_escaped}" sound name "{sound_effect}"'
    
    try:
        subprocess.run(["osascript", "-e", applescript_cmd], check=True)
        print("Đã gửi thông báo hệ thống thành công.")
    except Exception as e:
        print(f"Lỗi khi gửi thông báo macOS: {e}", file=sys.stderr)

def open_html_in_browser():
    """
    Mở file HTML báo cáo tin tức trong trình duyệt mặc định của macOS
    """
    try:
        subprocess.run(["open", OUTPUT_HTML], check=True)
        print("Đã mở bản tin HTML trên trình duyệt mặc định.")
    except Exception as e:
        print(f"Không thể mở file HTML: {e}", file=sys.stderr)

def main():
    print(f"Bắt đầu thu thập dữ liệu lúc {datetime.datetime.now()}...")
    
    # 1. Thu thập thời tiết 3 miền (có delay giữa các thành phố để tránh rate limit)
    weather_results = {}
    for i, (city, coords) in enumerate(CITIES.items()):
        if i > 0:
            time.sleep(1)  # Tránh gọi dồn dập gây lỗi 503
        weather_results[city] = get_weather_info(city, coords["lat"], coords["lon"])
        
    # 2. Thu thập và lọc tin tức theo các nhóm chuyên mục
    priority_news, weather_news, tech_news, ai_news, youth_news, wc_news, game_news = process_news_and_warnings()
    
    # 3. Tạo bản tin HTML Dashboard 3 cột
    build_html_report(weather_results, priority_news, weather_news, tech_news, ai_news, youth_news, wc_news, game_news)
    
    # 4. Gửi notification macOS
    has_warnings = len(priority_news) > 0
    send_macos_notification(weather_results, has_warnings)
    
    # 5. Tự động mở bản tin chi tiết trên trình duyệt để người dùng xem luôn
    open_html_in_browser()
    
    print("Hoàn thành tác vụ cập nhật tin tức.")

if __name__ == "__main__":
    main()
