import streamlit as st
from requests_html import HTMLSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json

def parse_og_metadata(url):
    debug_container = st.empty()
    session = HTMLSession()
    
    try:
        # Convert to mobile URL for Coupang
        if 'coupang.com' in url:
            url = url.replace('www.coupang.com', 'm.coupang.com')
            debug_container.info(f"Converting to mobile URL: {url}")
        
        # Mobile User-Agent and additional headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"iOS"',
        }
        
        debug_container.info("Sending request...")
        response = session.get(url, headers=headers)
        debug_container.info(f"Response status: {response.status_code}")
        
        # For debugging
        debug_container.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            debug_container.error(f"Failed with status code: {response.status_code}")
            debug_container.info(f"Response preview: {response.text[:500]}")
            return None
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        og_data = {
            'title': None,
            'description': None,
            'image': None,
            'site_name': None,
            'url': url
        }
        
        # Try different meta tag patterns
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        if not og_tags:
            og_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('og:')})
        
        debug_container.info(f"Found {len(og_tags)} OG tags")
        
        for tag in og_tags:
            property_name = tag.get('property', tag.get('name', '')).replace('og:', '')
            content = tag.get('content')
            
            if property_name in og_data:
                og_data[property_name] = content
                debug_container.info(f"Found {property_name}: {content[:100] if content else 'None'}...")
        
        # Handle relative image URLs
        if og_data['image'] and not og_data['image'].startswith(('http://', 'https://')):
            og_data['image'] = urljoin(url, og_data['image'])
        
        # Fallbacks
        if not og_data['title']:
            title_tag = soup.find('title')
            if title_tag:
                og_data['title'] = title_tag.string
            else:
                h1_tag = soup.find('h1')
                og_data['title'] = h1_tag.string if h1_tag else None
        
        if not og_data['description']:
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                og_data['description'] = meta_desc.get('content')
            else:
                meta_desc = soup.find('meta', {'name': 'Description'})
                og_data['description'] = meta_desc.get('content') if meta_desc else None
        
        # Check if we got any meaningful data
        if any(value for value in og_data.values()):
            debug_container.success("Successfully retrieved metadata!")
            return og_data
        else:
            debug_container.error("No metadata found in the page")
            return None
            
    except Exception as e:
        debug_container.error(f"""
        Error occurred:
        Type: {type(e).__name__}
        Message: {str(e)}
        """)
        return None
        
    finally:
        try:
            session.close()
        except:
            pass

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
    .example-link {
        word-break: break-all;
        padding: 5px;
        background-color: #ffffff;
        border-radius: 3px;
        margin: 5px 0;
        display: block;
    }
    .debug-info {
        font-family: monospace;
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title('🔍 URL OG 메타데이터 파서')

st.subheader('사이트 URL의 og 메타데이터를 파싱합니다.')

example_urls = [
    {
        "name": "네이버 뉴스",
        "url": "https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1=105"
    },
    {
        "name": "다음 뉴스",
        "url": "https://news.daum.net/"
    },
    {
        "name": "네이버 블로그",
        "url": "https://blog.naver.com/"
    }
]

for example in example_urls:
    st.markdown(f"""
    <div class="example-sites">
        <b>{example['name']}</b>
        <div class="example-link">
            {example['url']}
        </div>
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
    
    # Warning for certain sites
    if 'coupang.com' in url:
        st.info("쿠팡 URL을 모바일 버전으로 변환하여 시도합니다.")
    
    with st.expander("디버그 정보", expanded=True):
        st.markdown('<div class="debug-info">', unsafe_allow_html=True)
        result = parse_og_metadata(url)
        st.markdown('</div>', unsafe_allow_html=True)
        
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
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        st.download_button(
            label="JSON 다운로드",
            data=json_str,
            file_name="og_metadata.json",
            mime="application/json"
        )

st.markdown("""
---
by Richet
""")
