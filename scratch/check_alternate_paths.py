import requests
import re

BASE_URL = "https://www.twitch.tv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def main():
    r = requests.get(BASE_URL, headers=HEADERS)
    chunks = re.findall(r'(\d+):"([a-f0-9]{20})"', r.text)
    
    print(f"Testing chunk paths for first 10 chunks...")
    for cid, chash in chunks[:10]:
        # Path 1: assets/cid-chash.js
        url1 = f"https://assets.twitch.tv/assets/{cid}-{chash}.js"
        # Path 2: assets/chunks/cid-chash.js
        url2 = f"https://assets.twitch.tv/assets/chunks/{cid}-{chash}.js"
        # Path 3: assets/chunks/cid.js (without hash)
        url3 = f"https://assets.twitch.tv/assets/chunks/{cid}.js"
        
        status1 = requests.get(url1, headers=HEADERS).status_code
        status2 = requests.get(url2, headers=HEADERS).status_code
        
        print(f"Chunk {cid} (hash {chash}):")
        print(f"  Path 1 (/assets/): {status1}")
        print(f"  Path 2 (/assets/chunks/): {status2}")

if __name__ == "__main__":
    main()
