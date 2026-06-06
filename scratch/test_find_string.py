import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://www.twitch.tv"
ASSETS_BASE_URL = "https://assets.twitch.tv/assets"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def search_chunk(cid, chash):
    url = f"{ASSETS_BASE_URL}/{cid}-{chash}.js"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            if "ViewerDropsDashboard" in r.text:
                return cid, r.text
    except Exception:
        pass
    return cid, None

def main():
    print("Fetching manifest...")
    r = requests.get(BASE_URL, headers=HEADERS)
    chunks = re.findall(r'(\d+):"([a-f0-9]{20})"', r.text)
    print(f"Searching {len(chunks)} chunks for 'ViewerDropsDashboard'...")
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(search_chunk, cid, chash): cid for cid, chash in chunks}
        
        for future in as_completed(futures):
            cid, text = future.result()
            if text:
                print(f"\nFOUND ViewerDropsDashboard in chunk {cid}!")
                # Print 300 chars around it
                idx = text.find("ViewerDropsDashboard")
                print(text[max(0, idx-150):min(len(text), idx+150)])
                break
        else:
            print("\nViewerDropsDashboard was not found in any chunk!")

if __name__ == "__main__":
    main()
