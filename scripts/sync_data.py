import argparse
import os
import requests
import json

def sync_pubs():
    print("Syncing publications from Google Scholar...")
    # This would ideally use 'scholarly' or a BibTeX export.
    # For now, it scaffolds the 'content/publication/' directory.
    os.makedirs('content/publication', exist_ok=True)
    print("Placeholder: Publications sync logic goes here.")

def sync_github():
    print("Syncing GitHub stats...")
    username = "mbhall88"
    url = f"https://api.github.com/users/{username}"
    # Minimal stats fetch
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            stats = {
                "public_repos": data.get("public_repos"),
                "followers": data.get("followers"),
                "updated_at": data.get("updated_at")
            }
            os.makedirs('data', exist_ok=True)
            with open('data/github_stats.json', 'w') as f:
                json.dump(stats, f, indent=2)
            print(f"Saved stats to data/github_stats.json: {stats}")
        else:
            print(f"Failed to fetch GitHub stats: {response.status_code}")
    except Exception as e:
        print(f"Error fetching GitHub stats: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pubs", action="store_true")
    parser.add_argument("--github", action="store_true")
    args = parser.parse_args()

    if args.pubs:
        sync_pubs()
    if args.github:
        sync_github()
