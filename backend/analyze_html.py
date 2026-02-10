"""상명대학교 식단표 HTML 구조 분석"""
import requests
from bs4 import BeautifulSoup

def analyze_seoul():
    print("\n" + "="*80)
    print("📍 서울캠퍼스")
    print("="*80)
    
    url = 'https://www.smu.ac.kr/kor/life/restaurantView.do'
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tables = soup.find_all('table')
    print(f"\n총 {len(tables)}개 테이블")
    
    for i, table in enumerate(tables, 1):
        print(f"\n[테이블 {i}]")
        rows = table.find_all('tr')
        print(f"  행 수: {len(rows)}")
        
        for j, row in enumerate(rows[:5], 1):
            cells = row.find_all(['td', 'th'])
            texts = [c.get_text(strip=True)[:25] for c in cells[:4]]
            if any(texts):
                print(f"  행{j}: {texts}")

def analyze_cheonan():
    urls = {
        "천안_교직원": "https://www.smu.ac.kr/kor/life/restaurantView3.do",
        "천안_학생": "https://www.smu.ac.kr/kor/life/restaurantView4.do"
    }
    
    for name, url in urls.items():
        print("\n" + "="*80)
        print(f"📍 {name}")
        print("="*80)
        
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 테이블의 모든 행 확인
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            print(f"\n테이블 행 수: {len(rows)}")
            
            for i, row in enumerate(rows[:10], 1):
                cells = row.find_all(['td', 'th'])
                texts = [c.get_text(strip=True)[:30] for c in cells]
                if any(texts):
                    print(f"  행{i}: {texts}")
        
        # 이미지와 링크 확인
        print("\n🖼️ 이미지 링크:")
        imgs = soup.find_all('img', src=True)
        for img in imgs[:3]:
            print(f"  {img.get('src')[:70]}")
        
        print("\n📎 a 태그:")
        links = soup.find_all('a', href=True)[:10]
        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)[:30]
            if text:
                print(f"  [{text}] -> {href[:60]}")

if __name__ == "__main__":
    try:
        analyze_seoul()
        analyze_cheonan()
    except Exception as e:
        print(f"❌ 에러: {e}")
        import traceback
        traceback.print_exc()
