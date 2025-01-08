import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3
import time
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
]

user_agent_count = len(USER_AGENTS)
def parse_og_metadata(url, retry_count=user_agent_count):
    status_container = st.empty()
    
    for attempt in range(retry_count):
        try:
            # Customize headers based on the site
            if 'coupang.com' in url:
                headers = {
                    'User-Agent': USER_AGENTS[attempt],
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'Referer': 'https://www.google.com/',
                    'Cache-Control': 'max-age=0',
                }
                # Convert to mobile URL for Coupang
                url = url.replace('www.coupang.com', 'm.coupang.com')
            else:
                headers = {
                    'User-Agent': USER_AGENTS[attempt],
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'no-cache',
                }
            
            status_container.info(f"Attempt {attempt + 1} of {retry_count} with User-Agent: {USER_AGENTS[attempt][:50]}...")
            
            session = requests.Session()
            
            response = session.get(
                url, 
                headers=headers, 
                timeout=15,
                verify=False,
                allow_redirects=True
            )
            
            if response.status_code == 403:
                status_container.warning(f"Access forbidden (403). Trying next User-Agent...")
                time.sleep(2)
                continue
                
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            og_data = {
                'title': None,
                'description': None,
                'image': None,
                'site_name': None,
                'url': url
            }
            
            # Try multiple meta tag patterns
            og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
            if not og_tags:
                og_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('og:')})
            
            for tag in og_tags:
                property_name = tag.get('property', tag.get('name', '')).replace('og:', '')
                content = tag.get('content')
                
                if property_name in og_data:
                    og_data[property_name] = content
                    
            if og_data['image'] and not og_data['image'].startswith(('http://', 'https://')):
                og_data['image'] = urljoin(url, og_data['image'])
            
            # Enhanced fallbacks
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
                status_container.success(f"Successfully retrieved metadata with User-Agent #{attempt + 1}!")
                return og_data
            else:
                status_container.warning("No metadata found in this attempt...")
                time.sleep(2)
                continue
            
        except requests.Timeout:
            status_container.warning(f"Attempt {attempt + 1} timed out. Trying next User-Agent...")
            time.sleep(2)
            
        except requests.RequestException as e:
            status_container.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
            else:
                status_container.error("All User-Agents attempted without success.")
                return None
                
        except Exception as e:
            status_container.error(f"Unexpected error: {str(e)}")
            return None
        
        finally:
            try:
                session.close()
            except:
                pass

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
    .example-link {
        word-break: break-all;
        padding: 5px;
        background-color: #ffffff;
        border-radius: 3px;
        margin: 5px 0;
        display: block;
    }
    </style>
""", unsafe_allow_html=True)

st.title('🔍 URL OG 메타데이터 파서')

st.subheader('사이트 URL의 og 메타데이터 파싱 가능 여부를 파악할 수 있습니다.')

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
    if 'coupang.com' in url or 'gmarket.co.kr' in url:
        st.warning("쇼핑몰 사이트의 경우 보안 정책으로 인해 파싱이 제한될 수 있습니다.")
        
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
