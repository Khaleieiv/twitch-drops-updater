import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://www.twitch.tv"
ASSETS_BASE_URL = "https://assets.twitch.tv/assets"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def check_chunk(cid, chash):
    url = f"{ASSETS_BASE_URL}/{cid}-{chash}.js"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        return r.status_code
    except Exception as e:
        return str(type(e).__name__)

def main():
    r = requests.get(BASE_URL, headers=HEADERS)
    chunks = re.findall(r'(\d+):"([a-f0-9]{20})"', r.text)
    print(f"Checking first 100 chunks...")
    
    status_counts = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_chunk, cid, chash): cid for cid, chash in chunks[:100]}
        for future in as_completed(futures):
            status = future.result()
            status_counts[status] = status_counts.get(status, 0) + 1
            
    print("Status code counts for 100 requests:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")

if __name__ == "__main__":
    main()
