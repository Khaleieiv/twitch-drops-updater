import requests
import re

BASE_URL = "https://www.twitch.tv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def main():
    r = requests.get(BASE_URL, headers=HEADERS)
    
    # Search for all strings ending in .js in formulas, e.g. + ".js" or + '.js'
    matches = re.finditer(r'\+\s*["\']\.js["\']', r.text)
    print("Occurrences of + '.js' in HTML:")
    for m in matches:
        start = max(0, m.start() - 150)
        end = min(len(r.text), m.end() + 150)
        print(f"--- Context at {m.start()} ---")
        print(r.text[start:end])

if __name__ == "__main__":
    main()
