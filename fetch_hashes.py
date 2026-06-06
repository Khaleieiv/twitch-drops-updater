import re
import os
import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Target operations we need to keep updated
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

# Seed/Fallback hashes (from current working versions in Flutter codebase)
FALLBACK_HASHES = {
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
ASSETS_BASE_URL = "https://assets.twitch.tv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_initial_scripts():
    """Fetches Twitch homepage and extracts script URLs."""
    print("Fetching Twitch homepage...")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Twitch homepage: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    scripts = []
    for script in soup.find_all('script'):
        src = script.get('src')
        if src:
            if src.startswith('/'):
                scripts.append(BASE_URL + src)
            elif src.startswith('http'):
                scripts.append(src)
    
    # Filter scripts to only include Twitch asset scripts
    twitch_scripts = [s for s in scripts if "twitchsvc.net" in s or "/assets/" in s]
    print(f"Found {len(twitch_scripts)} initial scripts on homepage.")
    return twitch_scripts

def download_script(url):
    """Downloads script content."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return ""

def discover_chunks(js_content):
    """Finds webpack chunk filenames inside JavaScript code."""
    # Webpack chunks usually match: chunks/123-abcde123.js or name-hash.js
    # Standard format has 20 hex characters for the hash
    chunk_pattern = re.compile(r'["\'](assets/chunks/[a-zA-Z0-9_\-/]+-[a-f0-9]{20}\.js)["\']')
    chunks1 = chunk_pattern.findall(js_content)
    
    # Also find general webpack assets references
    general_pattern = re.compile(r'["\']([a-zA-Z0-9_\-/]+-[a-f0-9]{20}\.js)["\']')
    chunks2 = general_pattern.findall(js_content)
    
    # Combine and clean paths
    all_chunks = set(chunks1 + chunks2)
    cleaned_chunks = []
    for c in all_chunks:
        if c.startswith("assets/"):
            cleaned_chunks.append(f"{ASSETS_BASE_URL}/{c}")
        else:
            cleaned_chunks.append(f"{ASSETS_BASE_URL}/assets/{c}")
            
    return cleaned_chunks

def parse_hashes_from_js(js_content):
    """Searches JS content for GQL persisted query operation names and hashes."""
    found_hashes = {}
    
    # Pattern 1: {operationName:"Name",sha256Hash:"[hash]"} or id:"[hash]"
    pattern1 = re.compile(r'operationName\s*:\s*["\']([a-zA-Z0-9_]+)["\']\s*,\s*(?:sha256Hash|id)\s*:\s*["\']([a-f0-9]{32,64})["\']')
    for op_name, op_hash in pattern1.findall(js_content):
        found_hashes[op_name] = op_hash
        
    # Pattern 2: {sha256Hash:"[hash]",operationName:"Name"} or id:"[hash]"
    pattern2 = re.compile(r'(?:sha256Hash|id)\s*:\s*["\']([a-f0-9]{32,64})["\']\s*,\s*operationName\s*:\s*["\']([a-zA-Z0-9_]+)["\']')
    for op_hash, op_name in pattern2.findall(js_content):
        found_hashes[op_name] = op_hash

    # Pattern 3: operationName:"Name",...id:"[hash]" or similar
    # Less strict regex to find occurrences that might be slightly separated
    pattern3 = re.compile(r'operationName\s*:\s*["\']([a-zA-Z0-9_]+)["\'].{1,100}?(?:sha256Hash|id)\s*:\s*["\']([a-f0-9]{32,64})["\']')
    for op_name, op_hash in pattern3.findall(js_content):
        if op_name not in found_hashes:
            found_hashes[op_name] = op_hash
            
    return found_hashes

def main():
    print("--- Twitch GQL Hash Scraper Starting ---")
    
    # Load existing constants.json if it exists to preserve current values as default
    constants_file = "constants.json"
    hashes = {}
    if os.path.exists(constants_file):
        try:
            with open(constants_file, 'r', encoding='utf-8') as f:
                hashes = json.load(f)
            print(f"Loaded {len(hashes)} existing hashes from constants.json as baseline.")
        except Exception as e:
            print(f"Could not load existing constants.json: {e}")
            
    # Seed missing target operations with fallback defaults
    for op in TARGET_OPERATIONS:
        if op not in hashes:
            hashes[op] = FALLBACK_HASHES[op]

    # Step 1: Get initial scripts
    initial_scripts = get_initial_scripts()
    if not initial_scripts:
        print("No script URLs found. Exiting.")
        return
        
    # Step 2: Download initial scripts and discover chunks
    print("Downloading initial script files...")
    js_contents = []
    discovered_chunks = set()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download_script, url): url for url in initial_scripts}
        for future in as_completed(futures):
            url = futures[future]
            res = future.result()
            if res:
                js_contents.append(res)
                # Find other chunks referenced in these main script files
                chunks = discover_chunks(res)
                for chunk in chunks:
                    discovered_chunks.add(chunk)
                    
    print(f"Discovered {len(discovered_chunks)} potential Webpack chunk URLs.")
    
    # Step 3: Scan initial JS contents for hashes
    print("Scanning initial scripts for hashes...")
    for js in js_contents:
        found = parse_hashes_from_js(js)
        for op, h in found.items():
            if op in TARGET_OPERATIONS:
                hashes[op] = h
                
    # Step 4: Download and scan chunks in parallel to find missing hashes
    missing_ops = [op for op in TARGET_OPERATIONS if hashes[op] == FALLBACK_HASHES[op]]
    print(f"Remaining operations with default/fallback hashes: {missing_ops}")
    
    if missing_ops and discovered_chunks:
        print(f"Downloading and scanning {len(discovered_chunks)} chunks to locate missing hashes...")
        chunk_urls = list(discovered_chunks)
        
        # Download in chunks of threads to avoid rate limiting
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(download_script, url): url for url in chunk_urls}
            for future in as_completed(futures):
                url = futures[future]
                res = future.result()
                if res:
                    found = parse_hashes_from_js(res)
                    for op, h in found.items():
                        if op in TARGET_OPERATIONS:
                            if hashes[op] != h:
                                print(f"Found updated hash for {op}: {h} (was {hashes[op]})")
                                hashes[op] = h
                                
    # Print summary
    print("\n--- Summary of Results ---")
    updated_count = 0
    fallback_count = 0
    for op in TARGET_OPERATIONS:
        current = hashes[op]
        fallback = FALLBACK_HASHES[op]
        if current != fallback:
            print(f"[UPDATED] {op}: {current}")
            updated_count += 1
        else:
            print(f"[BASELINE/FALLBACK] {op}: {current}")
            fallback_count += 1
            
    print(f"Total: {len(TARGET_OPERATIONS)} operations. Updated: {updated_count}, Using Baseline: {fallback_count}")

    # Write output to constants.json
    try:
        with open(constants_file, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2)
        print(f"\nSuccessfully wrote hashes to '{constants_file}'.")
    except Exception as e:
        print(f"Error writing to constants.json: {e}")

if __name__ == "__main__":
    main()
