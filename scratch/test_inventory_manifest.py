import requests
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def main():
    print("Fetching drops inventory page...")
    r = requests.get("https://www.twitch.tv/drops/inventory", headers=HEADERS)
    
    # Check if ViewerDropsDashboard is directly in HTML
    print(f"Is 'ViewerDropsDashboard' in inventory HTML? {'ViewerDropsDashboard' in r.text}")
    
    # Extract chunk manifest from inventory page
    chunks = re.findall(r'(\d+):"([a-f0-9]{20})"', r.text)
    print(f"Found {len(chunks)} chunks in inventory manifest.")
    
    # Let's save a sample of the HTML to see what script tags are present
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, 'html.parser')
    scripts = [tag.get('src') for tag in soup.find_all('script') if tag.get('src')]
    print("Scripts loaded in HTML:")
    for s in scripts[:10]:
        print(f"  {s}")
        
if __name__ == "__main__":
    main()
