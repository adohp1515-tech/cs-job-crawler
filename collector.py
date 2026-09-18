# ============================================================================
# [collector.py] 잡코리아 & 알바몬 CS/콜센터 실제 채용 공고 자동 수집기
# ============================================================================
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. 갱신된 사용자 전용 구글 시트 클라우드 DB 연동 웹 앱 URL
GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwGdDo6ghU7sH2CH6jz5hCnXQPNs1JRxvMMR4raNHzofC2qtlmVBBoqCUZ-W9LiySw3/exec"

# 2. 아웃소싱 / 도급 / 파견사 배제 키워드 및 회사 블랙리스트
EXCLUDE_KEYWORDS = ["파견", "도급", "아웃소싱", "채용대행", "인력공급", "인재파견", "용역", "헤드헌팅", "위탁운영", "파견직", "도급직"]
EXCLUDE_COMPANIES = ["유베이스", "트랜스코스모스", "효성ITX", "케이티씨에스", "케이티아이에스", "삼구아이앤씨", "케이텍", "아데코", "맨파워", "제이엠씨"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

def is_outsourcing(title, company_name):
    """아웃소싱 및 파견사 공고 필터링"""
    text = f"{title} {company_name}"
    if any(comp in company_name for comp in EXCLUDE_COMPANIES):
        return True
    if any(kw in text for kw in EXCLUDE_KEYWORDS):
        return True
    return False

def extract_rep_email(homepage_url):
    """회사 홈페이지에서 대표 메일 자동 추출"""
    if not homepage_url or not homepage_url.startswith("http"):
        return "-"
    try:
        res = requests.get(homepage_url, headers=HEADERS, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', res.text)
        valid = [e for e in set(emails) if not e.endswith(('.png', '.jpg', '.gif', '.svg'))]
        for e in valid:
            if e.lower().startswith(('contact', 'info', 'help', 'cs', 'support', 'recruit')):
                return f"[대표] {e}"
        return f"[대표] {valid[0]}" if valid else "-"
    except Exception:
        return "-"

def send_to_cloud_db(lead):
    """구글 시트 클라우드 DB로 데이터 전송"""
    try:
        res = requests.post(GOOGLE_WEBAPP_URL, json=lead, timeout=10)
        print(f"[{lead['company']}] DB 전송 결과: {res.text}")
    except Exception as e:
        print(f"전송 실패 ({lead['company']}): {e}")

def crawl_jobkorea(keyword="CS상담"):
    """잡코리아 신규 공고 수집"""
    print(f">> [잡코리아] 검색 수집 중: {keyword}")
    url = f"https://www.jobkorea.co.kr/Search/?stext={keyword}&tabType=recruit"
    results = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select(".list-post .post-item") or soup.select(".list-item")
        
        for item in items[:15]:
            title_tag = item.select_one("a.title") or item.select_one(".post-list-info a")
            comp_tag = item.select_one("a.name") or item.select_one(".post-list-corp a")
            if not title_tag or not comp_tag:
                continue
            
            title = title_tag.get_text(strip=True)
            company = comp_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if link and link.startswith("/"):
                link = "https://www.jobkorea.co.kr" + link
            
            # 아웃소싱 필터링
            if is_outsourcing(title, company):
                continue
            
            job_id = "JK_" + re.sub(r'[^0-9]', '', link)[-8:] if re.search(r'\d+', link) else f"JK_{int(time.time())}"

            results.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "platform": "잡코리아",
                "company": company,
                "homepage": "",
                "title": title,
                "keyword": keyword,
                "task": "고객센터 인바운드/상담원 채용",
                "headcount": "0명",
                "location": "서울/수도권",
                "email": "-",
                "phone": "-",
                "link": link,
                "jobId": job_id,
                "is_outsourcing": False
            })
    except Exception as e:
        print(f"잡코리아 수집 에러: {e}")
    return results

def crawl_albamon(keyword="콜센터"):
    """알바몬 신규 공고 수집"""
    print(f">> [알바몬] 검색 수집 중: {keyword}")
    url = f"https://www.albamon.com/search?keyword={keyword}"
    results = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select(".g-list-item") or soup.select("li.c-list-item")
        
        for item in items[:15]:
            title_tag = item.select_one("a.c-list-item__title") or item.select_one(".title a")
            comp_tag = item.select_one(".c-list-item__corp") or item.select_one(".corp")
            if not title_tag or not comp_tag:
                continue
            
            title = title_tag.get_text(strip=True)
            company = comp_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if link and not link.startswith("http"):
                link = "https://www.albamon.com" + link
            
            # 아웃소싱 필터링
            if is_outsourcing(title, company):
                continue
            
            job_id = "AM_" + re.sub(r'[^0-9]', '', link)[-8:] if re.search(r'\d+', link) else f"AM_{int(time.time())}"

            results.
