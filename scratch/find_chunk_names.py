import requests
import re

BASE_URL = "https://www.twitch.tv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def main():
    r = requests.get(BASE_URL, headers=HEADERS)
    
    # Let's search for chunk 8 in the HTML page and print the line/context where it appears
    # outside of the hash dictionary
    matches = re.finditer(r'8\s*:', r.text)
    print("Occurrences of '8:' in HTML:")
    for m in matches:
        start = max(0, m.start() - 100)
        end = min(len(r.text), m.end() + 100)
        print(f"--- Context at {m.start()} ---")
        print(r.text[start:end])
        
if __name__ == "__main__":
    main()
