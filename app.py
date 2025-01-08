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
            
            # Increased timeout and added verify=False for SSL issues
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
            
            # Find all meta tags with og: prefix
            og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
            
            # Extract og metadata
            for tag in og_tags:
                property_name = tag.get('property', '').replace('og:', '')
                content = tag.get('content')
                
                if property_name in og_data:
                    og_data[property_name] = content
                    
            # If og:image is relative URL, make it absolute
            if og_data['image'] and not og_data['image'].startswith(('http://', 'https://')):
                og_data['image'] = urljoin(url, og_data['image'])
            
            # Fallbacks if og tags are not found
            if not og_data['title']:
                og_data['title'] = soup.title.string if soup.title else None
                
            if not og_data['description']:
                meta_desc = soup.find('meta', {'name': 'description'})
                og_data['description'] = meta_desc['content'] if meta_desc else None
                
            return og_data
            
        except requests.Timeout:
            st.warning(f"Attempt {attempt + 1} timed out. Retrying...")
            time.sleep(2)
            
        except requests.RequestException as e:
            st.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
            else:
                st.error("All retry attempts failed.")
                return None
                
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None

# Set page config
st.set_page_config(
    page_title="OG Metadata Parser",
    page_icon="🔍",
    layout="wide"
)

# Add custom CSS
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
    </style>
""", unsafe_allow_html=True)

# Main app
st.title('🔍 Open Graph Metadata Parser')
st.markdown("""
    This tool extracts Open Graph metadata from any website URL.
    Just enter a URL below and click 'Parse Metadata'.
""")

# Create two columns
col1, col2 = st.columns([2, 1])

with col1:
    url = st.text_input('Enter URL:', placeholder='https://example.com')
    
with col2:
    parse_button = st.button('Parse Metadata', type='primary')

if url and parse_button:
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    with st.spinner('Fetching metadata...'):
        result = parse_og_metadata(url)
        
    if result:
        st.markdown("<div class='output-container'>", unsafe_allow_html=True)
        
        # Display basic metadata
        st.subheader('📊 Metadata Results')
        
        # Create columns for organized display
        meta_col1, meta_col2 = st.columns(2)
        
        with meta_col1:
            st.markdown("**Title:**")
            st.write(result['title'] if result['title'] else 'Not found')
            
            st.markdown("**Description:**")
            st.write(result['description'] if result['description'] else 'Not found')
            
            st.markdown("**Site Name:**")
            st.write(result['site_name'] if result['site_name'] else 'Not found')
            
        with meta_col2:
            st.markdown("**URL:**")
            st.write(result['url'])
            
            if result['image']:
                st.markdown("**Image URL:**")
                st.write(result['image'])
        
        # Display the OG image if available
        if result['image']:
            st.subheader('📷 Preview Image')
            try:
                st.image(result['image'], use_column_width=True)
            except Exception as e:
                st.error(f"Failed to load image: {str(e)}")
                
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Add export options
        st.subheader('📤 Export Options')
        # Convert result to JSON string
        import json
        json_str = json.dumps(result, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name="og_metadata.json",
            mime="application/json"
        )
        
    else:
        st.error('Failed to retrieve metadata. Please check the URL and try again.')

# Footer
st.markdown("""
---
Made with ❤️ using Streamlit
""")
