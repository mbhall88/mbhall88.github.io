import argparse
import os
import requests
import json
import re

def sync_pubs():
    print("Syncing publications from ORCID...")
    os.makedirs('content', exist_ok=True)
    
    orcid = "0000-0003-3683-6208"
    url = f"https://pub.orcid.org/v3.0/{orcid}/works"
    headers = {"Accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        seen_titles = set()
        pubs = []
        
        for group in data.get('group', []):
            summary = group['work-summary'][0]
            work_type = summary.get('type', '')
            if work_type not in ['journal-article', 'preprint']:
                continue
                
            title = summary.get('title', {}).get('title', {}).get('value', 'Unknown')
            norm = re.sub(r'[^a-z0-9]', '', title.lower())
            if norm in seen_titles: continue
            seen_titles.add(norm)
            
            pd = summary.get('publication-date', {})
            year = pd.get('year', {}).get('value', '2023') if pd else '2023'
            venue = summary.get('journal-title', {}).get('value', 'Unknown Venue') if summary.get('journal-title') else 'Unknown Venue'
            
            # ORCID external IDs (DOI)
            doi = ""
            if summary.get('external-ids') and summary['external-ids'].get('external-id'):
                for ext in summary['external-ids']['external-id']:
                    if ext['external-id-type'] == 'doi':
                        doi = ext['external-id-value']
                        break
            
            pubs.append({'year': year, 'title': title, 'venue': venue, 'doi': doi, 'type': work_type})
            
        pubs.sort(key=lambda x: x['year'], reverse=True)
        
        with open('content/publications.md', 'w', encoding='utf-8') as f:
            f.write("---\ntitle: \"Publications\"\nlayout: \"archives\"\n---\n\n")
            f.write("A list of my research publications, automatically synced from my [ORCID](https://orcid.org/0000-0003-3683-6208).\n\n")
            for p in pubs[:20]:
                doi_link = f" [DOI: {p['doi']}](https://doi.org/{p['doi']})" if p['doi'] else ""
                type_badge = " *(Preprint)*" if p['type'] == 'preprint' else ""
                f.write(f"- **{p['title']}** ({p['year']}) - *{p['venue']}*{type_badge}{doi_link}\n")
        print("Updated content/publications.md")
    except Exception as e:
        print(f"Error: {e}")

def sync_github():
    print("Syncing GitHub stats...")
    username = "mbhall88"
    url = f"https://api.github.com/users/{username}"
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
