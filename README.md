# Twitch Drops Loot - Updater (GQL Hashes Auto-Update)

This project contains an automated Twitch GraphQL hash scraper and a pre-configured GitHub Actions Workflow. It scans Twitch's client scripts, extracts the latest SHA-256 hashes for persisted queries, and saves them in `constants.json`.

This allows the Flutter application to pull fresh hashes dynamically without needing a rebuild.

---

## How to Set Up on GitHub

To enable automated updates on a schedule:

### Step 1: Create a GitHub Repository
1. Go to [github.com](https://github.com) and create a new public or private repository (e.g., `twitch-drops-updater`).
2. Initialize the repository and upload the files from this folder (`twitch_drops_updater`) there:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/Khaleieiv/twitch-drops-updater.git
   git push -u origin main
   ```

### Step 2: Enable Write Permissions for GitHub Actions (IMPORTANT!)
By default, GitHub Actions do not have permissions to make commits and push changes back to the repository. To allow the script to automatically commit the updated `constants.json`:
1. Open your repository on GitHub.
2. Navigate to **Settings** -> **Actions** -> **General**.
3. Scroll down to the **Workflow permissions** section.
4. Select **Read and write permissions**.
5. Click **Save**.

---

## How It Works

* The workflow runs **every day at 00:00 UTC** (you can also trigger it manually under **Actions** -> **Update Twitch GQL Hashes** -> **Run workflow**).
* The `fetch_hashes.py` script downloads the main Twitch page, parses the links to all JS bundles, downloads them in parallel, and extracts the current hashes.
* If any hashes have changed, GitHub Actions automatically commits them with the message `chore: auto-update twitch gql hashes [skip ci]`.
* The raw URL of your JSON file will remain static:
  `https://raw.githubusercontent.com/Khaleieiv/twitch-drops-updater/main/constants.json`
