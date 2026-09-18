import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import urllib.parse

# 1. 구글 Apps Script 웹 앱 URL
GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwGdDo6ghU7sH2CH6jz5hCnXQPNs1JRxvMMR4raNHzofC2qtlmVBBoqCUZ-W9LiySw3/exec"

# 2. 아웃소싱 / 도급사 배제 키워드 및 블랙리스트
EXCLUDE_KEYWORDS = ["파견", "도급", "아웃소싱", "채용대행", "인력공급", "인재파견", "용역", "헤드헌팅", "위탁운영", "파견직", "도급직"]
EXCLUDE_COMPANIES = ["유베이스", "트랜스코스모스", "효성ITX", "케이티씨에스", "케이티아이에스", "삼구아이앤씨", "케이텍", "아데코", "맨파워", "제이엠씨"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

def is_outsourcing(title, company_name):
    text = f"{title} {company_name}"
    if any(comp in company_name for comp in EXCLUDE_COMPANIES):
        return True
    if any(kw in text for kw in EXCLUDE_KEYWORDS):
        return True
    return False

def send_to_cloud_db(lead):
    try:
        res = requests.post(GOOGLE_WEBAPP_URL, json=lead, timeout=10)
        print(f"[{lead['company']}] DB 전송 결과: {res.text}")
    except Exception as e:
        print(f"전송 실패 ({lead['company']}): {e}")

def crawl_jobkorea(keyword="CS상담"):
    print(f">> [잡코리아] 검색 수집 중: {keyword}")
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://www.jobkorea.co.kr/Search/?stext={encoded_kw}&tabType=recruit"
    results = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select(".list-post .post-item") or soup.select(".list-item")
        
        for item in items[:10]:
            title_tag = item.select_one("a.title") or item.select_one(".post-list-info a")
            comp_tag = item.select_one("a.name") or item.select_one(".post-list-corp a")
            if not title_tag or not comp_tag:
                continue
            
            title = title_tag.get_text(strip=True)
            company = comp_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if link and link.startswith("/"):
                link = "https://www.jobkorea.co.kr" + link
            
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
        print(f"잡코리아 수집 에러 (무시하고 계속 진행): {e}")
    return results

def crawl_albamon(keyword="콜센터"):
    print(f">> [알바몬] 검색 수집 중: {keyword}")
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://www.albamon.com/search?keyword={encoded_kw}"
    results = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select(".g-list-item") or soup.select("li.c-list-item")
        
        for item in items[:10]:
            title_tag = item.select_one("a.c-list-item__title") or item.select_one(".title a")
            comp_tag = item.select_one(".c-list-item__corp") or item.select_one(".corp")
            if not title_tag or not comp_tag:
                continue
            
            title = title_tag.get_text(strip=True)
            company = comp_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            if link and not link.startswith("http"):
                link = "https://www.albamon.com" + link
            
            if is_outsourcing(title, company):
                continue
            
            job_id = "AM_" + re.sub(r'[^0-9]', '', link)[-8:] if re.search(r'\d+', link) else f"AM_{int(time.time())}"

            results.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "platform": "알바몬",
                "company": company,
                "homepage": "",
                "title": title,
                "keyword": keyword,
                "task": "CS 고객상담 및 인바운드 접수",
                "headcount": "0명",
                "location": "서울/수도권",
                "email": "-",
                "phone": "-",
                "link": link,
                "jobId": job_id,
                "is_outsourcing": False
            })
    except Exception as e:
        print(f"알바몬 수집 에러 (무시하고 계속 진행): {e}")
    return results

def main():
    try:
        print("=== BPO 영업 파이프라인 실제 크롤러 가동 ===")
        all_leads = []
        
        for kw in ["CS상담", "콜센터", "상담사"]:
            all_leads.extend(crawl_jobkorea(kw))
            all_leads.extend(crawl_albamon(kw))
            time.sleep(1)
            
        print(f"필터 통과 유효 리드: 총 {len(all_leads)}건. 구글 시트 클라우드 DB로 전송합니다.")
        
        for lead in all_leads:
            send_to_cloud_db(lead)
            time.sleep(0.5)
            
        print("=== 크롤러 정상 완료 ===")
    except Exception as e:
        print(f"전체 프로세스 에러 발생: {e}")

if __name__ == "__main__":
    main()
