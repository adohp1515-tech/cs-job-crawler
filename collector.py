import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# 1. 구글 시트 Apps Script 웹 앱 URL (사전 준비에서 복사한 URL)
GOOGLE_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzdsEkh1Tvyrq4RTMcc1RZHHiEYheEsemCX3Vg243hD_qyhVx_h--pWrAzsVShs2mEn/exec"

# 2. 아웃소싱 / 도급 제외 키워드 및 블랙리스트
EXCLUDE_KEYWORDS = ["파견", "도급", "아웃소싱", "채용대행", "인력공급", "인재파견", "용역", "헤드헌팅", "위탁"]
EXCLUDE_COMPANIES = ["유베이스", "트랜스코스모스", "효성ITX", "케이티씨에스", "케이티아이에스", "삼구아이앤씨", "케이텍"]

def is_outsourcing(title, company_name):
    """아웃소싱/도급사 여부 판별"""
    text = f"{title} {company_name}"
    if any(c in company_name for c in EXCLUDE_COMPANIES):
        return True
    if any(k in text for k in EXCLUDE_KEYWORDS):
        return True
    return False

def extract_rep_email(homepage_url):
    """회사 홈페이지에서 대표 메일 추출"""
    if not homepage_url or not homepage_url.startswith("http"):
        return "-"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(homepage_url, headers=headers, timeout=5)
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', res.text)
        valid = [e for e in set(emails) if not e.endswith(('.png', '.jpg', '.gif', '.svg'))]
        for e in valid:
            if e.lower().startswith(('contact', 'info', 'help', 'cs', 'support', 'recruit')):
                return f"[대표] {e}"
        return f"[대표] {valid[0]}" if valid else "-"
    except Exception:
        return "-"

def send_to_google_sheets(item):
    """구글 시트 웹앱으로 데이터 전송"""
    try:
        res = requests.post(GOOGLE_WEBAPP_URL, json=item, timeout=10)
        print(f"[{item['company']}] 시트 전송 결과: {res.text}")
    except Exception as e:
        print(f"전송 실패: {e}")

def main():
    print("=== 채용 공고 수집 및 파이프라인 전송 시작 ===")
    
    # 예시: 플랫폼별 수집 로직이 발굴한 데이터 목록 (실제 사이트 검색결과 연동)
    # 잡코리아/알바몬/알바천국 신규 공고 예시
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    leads = [
        {
            "date": current_time,
            "platform": "잡코리아",
            "company": "배민로지스틱스",
            "homepage": "https://www.woowahan.com",
            "title": "라이더 CS 지원 및 인바운드 관제 상담원 채용",
            "keyword": "CS상담",
            "task": "라이더 배송 문의 유선 상담 및 배송 이슈 모니터링",
            "headcount": "3명",
            "location": "서울 송파구",
            "email": "", # 메일 부재 시 홈페이지에서 대표메일 추출
            "phone": "1600-0987",
            "link": "https://www.jobkorea.co.kr",
            "jobId": "JK_" + datetime.now().strftime("%m%d%H%M") + "_01"
        }
    ]

    for lead in leads:
        # 아웃소싱/도급사 제외 필터링
        if is_outsourcing(lead["title"], lead["company"]):
            print(f"제외됨 (아웃소싱/도급): {lead['company']}")
            continue
            
        # 이메일 부재 시 회사 홈페이지 대표메일 크롤링
        if not lead.get("email"):
            lead["email"] = extract_rep_email(lead.get("homepage"))
            
        # 구글 시트로 행 전송
        send_to_google_sheets(lead)

if __name__ == "__main__":
    main()
