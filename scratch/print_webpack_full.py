import requests
import re

BASE_URL = "https://www.twitch.tv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def main():
    r = requests.get(BASE_URL, headers=HEADERS)
    
    # Let's search for }[e]+".js"
    idx = r.text.find('}[e]+".js"')
    if idx != -1:
        print("--- Webpack JS Chunk Function Context ---")
        start = max(0, idx - 1000)
        end = min(len(r.text), idx + 200)
        print(r.text[start:end])
    else:
        print("Not found }[e]+\".js\"")

if __name__ == "__main__":
    main()
