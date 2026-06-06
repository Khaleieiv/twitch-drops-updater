import requests
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Target GQL hashes from gql_operations.dart
TARGET_HASHES = {
    "ViewerDropsDashboard": "5a4da2ab3d5b47c9f9ce864e727b2cb346af1e3ea8b897fe8f704a97ff017619",
    "DropCampaignDetails": "039277bf98f3130929262cc7c6efd9c141ca3749cb6dca442fc8ead9a53f77c1",
    "Inventory": "d86775d0ef16a63a33ad52e80eaff963b2d5b72fada7c991504a57496e1d8e4b",
    "DropCurrentSessionContext": "4d06b702d25d652afb9ef835d2a550031f1cf762b193523a92166f40ea3d142b",
    "DropsPage_ClaimDropRewards": "a455deea71bdc9015b78eb49f4acfbce8baa7ccbedd28e549bb025bd0f751930",
    "DirectoryPage_Game": "cb5dc816e139dcb8a118f14b4b677d59abc224a4b016c4bc2bb00a47fe0ddec4",
    "VideoPlayerStreamInfoOverlayChannel": "198492e0857f6aedead9665c81c5a06d67b25b58034649687124083ff288597d",
    "DropsHighlightService_AvailableDrops": "782dad0f032942260171d2d80a654f88bdd0c5a9dddc392e9bc92218a0f42d20",
}

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
            found = []
            for name, h in TARGET_HASHES.items():
                if h in r.text:
                    found.append((name, h))
            if found:
                return cid, found, r.text
    except Exception:
        pass
    return cid, [], ""

def main():
    r = requests.get(BASE_URL, headers=HEADERS)
    chunks = re.findall(r'(\d+):"([a-f0-9]{20})"', r.text)
    print(f"Searching {len(chunks)} chunks for target hashes...")
    
    found_count = 0
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(search_chunk, cid, chash): cid for cid, chash in chunks}
        
        for future in as_completed(futures):
            cid, found, text = future.result()
            if found:
                for name, h in found:
                    print(f"\nFOUND hash for {name} ({h}) in chunk {cid}!")
                    idx = text.find(h)
                    print(text[max(0, idx-150):min(len(text), idx+150)])
                    found_count += 1
                    
    print(f"\nSearch finished. Found {found_count} hashes in total.")

if __name__ == "__main__":
    main()
