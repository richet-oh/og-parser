import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add proxy support
proxies = {
    'http': None,
    'https': None
}

# Configure requests to disable SSL verification globally
requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
]

user_agent_count = len(USER_AGENTS)
def parse_og_metadata(url, retry_count=user_agent_count):
    debug_container = st.empty()
    
    for attempt in range(retry_count):
        try:
            headers = {
                'User-Agent': USER_AGENTS[attempt],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            debug_container.info(f"Attempt {attempt + 1} of {retry_count} with User-Agent: {USER_AGENTS[attempt][:50]}...")
            
            # Add proxies and SSL verification disable
            response = requests.get(
                url, 
                headers=headers, 
                timeout=15,
                verify=False,
                allow_redirects=True,
                proxies=proxies
            )
            
            debug_container.info(f"Response Status: {response.status_code}")
            debug_container.info(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                debug_container.warning(f"Failed with status {response.status_code}, trying next User-Agent...")
                debug_container.info(f"Response Content Preview: {response.text[:500]}")
                time.sleep(2)
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            og_data = {
                'title': None,
                'description': None,
                'image': None,
                'site_name': None,
                'url': url
            }
            
            og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
            debug_container.info(f"Found {len(og_tags)} OG tags")
            
            for tag in og_tags:
                property_name = tag.get('property', '').replace('og:', '')
                content = tag.get('content')
                
                if property_name in og_data:
                    og_data[property_name] = content
                    debug_container.info(f"Found {property_name}: {content[:100] if content else None}")
                    
            if og_data['image'] and not og_data['image'].startswith(('http://', 'https://')):
                og_data['image'] = urljoin(url, og_data['image'])
            
            if not og_data['title']:
                og_data['title'] = soup.title.string if soup.title else None
                
            if not og_data['description']:
                meta_desc = soup.find('meta', {'name': 'description'})
                og_data['description'] = meta_desc['content'] if meta_desc else None
                
            if any(value for value in og_data.values()):
                debug_container.success(f"Successfully retrieved metadata with User-Agent #{attempt + 1}")
                return og_data
            else:
                debug_container.warning("No metadata found, trying next User-Agent...")
                time.sleep(2)
                continue
            
        except requests.Timeout:
            debug_container.warning(f"Attempt {attempt + 1} timed out. Trying next User-Agent...")
            time.sleep(2)
            
        except requests.RequestException as e:
            debug_container.warning(f"""
            Attempt {attempt + 1} failed:
            Error Type: {type(e).__name__}
            Error Message: {str(e)}
            """)
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
            else:
                debug_container.error("All User-Agents attempted without success.")
                return None
                
        except Exception as e:
            debug_container.error(f"""
            Unexpected error:
            Error Type: {type(e).__name__}
            Error Message: {str(e)}
            """)
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

st.subheader('사이트 URL의 og 메타데이터를 파싱합니다.')

example_urls = [
    {
        "name": "네이버 뉴스",
        "url": "https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1=105"
    },
    {
        "name": "다음 뉴스",
        "url": "https://news.daum.net/"
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
        
    with st.expander("진행 상황", expanded=True):
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
