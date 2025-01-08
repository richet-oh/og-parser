import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import random
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# List of common user agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

def parse_og_metadata(url, retry_count=3):
    for attempt in range(retry_count):
        try:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=15,
                verify=False,
                allow_redirects=True
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            og_data = {
                'title': None,
                'description': None,
                'image': None,
                'site_name': None,
                'url': url
            }
            
            og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
            
            for tag in og_tags:
                property_name = tag.get('property', '').replace('og:', '')
                content = tag.get('content')
                
                if property_name in og_data:
                    og_data[property_name] = content
                    
            if og_data['image'] and not og_data['image'].startswith(('http://', 'https://')):
                og_data['image'] = urljoin(url, og_data['image'])
            
            if not og_data['title']:
                og_data['title'] = soup.title.string if soup.title else None
                
            if not og_data['description']:
                meta_desc = soup.find('meta', {'name': 'description'})
                og_data['description'] = meta_desc['content'] if meta_desc else None
                
            return og_data
            
        except requests.Timeout:
            st.warning(f"시도 {attempt + 1}가 시간 초과되었습니다. 다시 시도중...")
            time.sleep(2)
            
        except requests.RequestException as e:
            st.warning(f"시도 {attempt + 1} 실패: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
            else:
                st.error("모든 시도가 실패했습니다.")
                return None
                
        except Exception as e:
            st.error(f"예상치 못한 오류: {str(e)}")
            return None

st.set_page_config(
    page_title="OG 메타데이터 파서",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .output-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    .example-sites {
        background-color: #e1e5eb;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title('🔍 URL 메타데이터 파서')

# Example sites section
st.subheader('사이트 URL 파싱 예시 사이트')
st.markdown("""
<div class="example-sites">
<b>뉴스 사이트:</b>
- https://www.chosun.com
- https://www.hani.co.kr
- https://www.yna.co.kr

<b>쇼핑몰:</b>
- https://www.coupang.com
- https://www.gmarket.co.kr
- https://www.11st.co.kr

<b>SNS:</b>
- https://twitter.com
- https://www.instagram.com
- https://www.facebook.com
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    url = st.text_input('URL 입력:', placeholder='https://example.com')
    
with col2:
    parse_button = st.button('메타데이터 파싱', type='primary')

if url and parse_button:
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    with st.spinner('메타데이터 가져오는 중...'):
        result = parse_og_metadata(url)
        
    if result:
        st.markdown("<div class='output-container'>", unsafe_allow_html=True)
        
        st.subheader('📊 메타데이터 결과')
        
        meta_col1, meta_col2 = st.columns(2)
        
        with meta_col1:
            st.markdown("**제목:**")
            st.write(result['title'] if result['title'] else '없음')
            
            st.markdown("**설명:**")
            st.write(result['description'] if result['description'] else '없음')
            
            st.markdown("**사이트명:**")
            st.write(result['site_name'] if result['site_name'] else '없음')
            
        with meta_col2:
            st.markdown("**URL:**")
            st.write(result['url'])
            
            if result['image']:
                st.markdown("**이미지 URL:**")
                st.write(result['image'])
        
        if result['image']:
            st.subheader('📷 미리보기 이미지')
            try:
                st.image(result['image'], use_column_width=True)
            except Exception as e:
                st.error(f"이미지 로드 실패: {str(e)}")
                
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.subheader('📤 내보내기 옵션')
        import json
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        st.download_button(
            label="JSON 다운로드",
            data=json_str,
            file_name="og_metadata.json",
            mime="application/json"
        )
        
    else:
        st.error('메타데이터를 가져오지 못했습니다. URL을 확인하고 다시 시도해주세요.')

st.markdown("""
---
Streamlit으로 제작됨 ❤️
""")
