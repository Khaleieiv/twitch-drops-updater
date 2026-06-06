import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

TARGET_OPERATIONS = [
    "ViewerDropsDashboard",
    "DropCampaignDetails",
    "Inventory",
    "DropCurrentSessionContext",
    "DropsPage_ClaimDropRewards",
    "DirectoryPage_Game",
    "VideoPlayerStreamInfoOverlayChannel",
    "DropsHighlightService_AvailableDrops",
]

BASE_URL = "https://www.twitch.tv"
ASSETS_BASE_URL = "https://assets.twitch.tv/assets"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def parse_hashes(js_text):
    found = {}
    pattern1 = re.compile(r'operationName\s*:\s*["\']([a-zA-Z0-9_]+)["\']\s*,\s*(?:sha256Hash|id)\s*:\s*["\']([a-f0-9]{32,64})["\\\]?["\']')
    for op_name, op_hash in pattern1.findall(js_text):
        found[op_name] = op_hash
    pattern2 = re.compile(r'(?:sha256Hash|id)\s*:\s*["\']([a-f0-9]{32,64})["\']\s*,\s*operationName\s*:\s*["\']([a-zA-Z0-9_]+)["\']')
    for op_hash, op_name in pattern2.findall(js_text):
        found[op_name] = op_hash
    return found

def download_and_scan(chunk_id, chunk_hash):
    url = f"{ASSETS_BASE_URL}/{chunk_id}-{chunk_hash}.js"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            found = parse_hashes(r.text)
            # Filter to only target operations
            filtered = {k: v for k, v in found.items() if k in TARGET_OPERATIONS}
            if filtered:
                return chunk_id, filtered
    except Exception:
        pass
    return chunk_id, None

def main():
    print("Fetching homepage to get chunk manifest...")
    r = requests.get(BASE_URL, headers=HEADERS)
    chunks = re.findall(r'(\d+):"([a-f0-9]{20})"', r.text)
    print(f"Found {len(chunks)} chunks in manifest.")
    
    # We will search in parallel
    found_hashes = {}
    start_time = time.time()
    
    # Use 50 threads to download chunks in parallel
    max_threads = 50
    print(f"Starting scan using {max_threads} threads...")
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(download_and_scan, cid, chash): cid for cid, chash in chunks}
        
        completed_count = 0
        for future in as_completed(futures):
            completed_count += 1
            cid, result = future.result()
            if result:
                for op, h in result.items():
                    if op not in found_hashes:
                        print(f"[{completed_count}/{len(chunks)}] Found {op}: {h} in chunk {cid}")
                        found_hashes[op] = h
                        
                # Check if we have found all targets
                if all(op in found_hashes for op in TARGET_OPERATIONS):
                    print("All target hashes found! Stopping search.")
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    break
                    
            if completed_count % 100 == 0:
                print(f"Scanned {completed_count}/{len(chunks)} chunks... Found {len(found_hashes)}/{len(TARGET_OPERATIONS)} targets.")
                
    elapsed = time.time() - start_time
    print(f"\nScan completed in {elapsed:.2f} seconds.")
    print(f"Found {len(found_hashes)} of {len(TARGET_OPERATIONS)} targets:")
    for op in TARGET_OPERATIONS:
        print(f"  {op}: {found_hashes.get(op, 'NOT FOUND')}")

if __name__ == "__main__":
    main()
