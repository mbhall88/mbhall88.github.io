import argparse
import os
import requests
import json
import re

def sync_pubs():
    print("Syncing publications from ORCID...")
    os.makedirs('content/publications', exist_ok=True)
    
    orcid = "0000-0003-3683-6208"
    url = f"https://pub.orcid.org/v3.0/{orcid}/works"
    headers = {"Accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        seen_titles = set()
        
        # Get groups and sort by year (descending) if available
        groups = data.get('group', [])
        
        pubs_to_process = []
        for group in groups:
            summary = group['work-summary'][0]
            title = summary.get('title', {}).get('title', {}).get('value', 'Unknown Title')
            
            # Normalize title to check for duplicates
            norm_title = re.sub(r'[^a-z0-9]', '', title.lower())
            if norm_title in seen_titles:
                continue
            seen_titles.add(norm_title)
            
            pub_date = summary.get('publication-date', {})
            if pub_date:
                year = pub_date.get('year', {}).get('value', '2023') if pub_date.get('year') else '2023'
                month = pub_date.get('month', {}).get('value', '01') if pub_date.get('month') else '01'
                day = pub_date.get('day', {}).get('value', '01') if pub_date.get('day') else '01'
            else:
                year, month, day = '2023', '01', '01'
                
            journal = summary.get('journal-title', {}).get('value', '') if summary.get('journal-title') else 'Unknown Venue'
            
            pubs_to_process.append({
                'title': title,
                'year': year,
                'month': month,
                'day': day,
                'venue': journal,
                'abstract': '' # ORCID summary doesn't always have abstract easily
            })
            
        # Sort descending
        pubs_to_process.sort(key=lambda x: (x['year'], x['month'], x['day']), reverse=True)
        
        for pub in pubs_to_process[:15]: # Keep top 15
            title = pub['title']
            year = pub['year']
            month = pub['month']
            day = pub['day']
            venue = pub['venue']
            
            safe_title = "".join([c if c.isalnum() else "-" for c in title.lower()])
            safe_title = "-".join(filter(None, safe_title.split("-")))[:50]
            
            pub_dir = f"content/publications/{safe_title}"
            os.makedirs(pub_dir, exist_ok=True)
            
            index_path = os.path.join(pub_dir, "index.md")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("---\n")
                clean_title = title.replace('"', '')
                f.write(f"title: \"{clean_title}\"\n")
                f.write(f"date: {year}-{month}-{day}\n")
                f.write(f"publishDate: {year}-{month}-{day}\n")
                f.write("authors:\n- \"admin\"\n")
                
                clean_venue = venue.replace('"', '')
                if clean_venue:
                    f.write(f"publication: \"{clean_venue}\"\n")
                
                f.write("abstract: \"\"\n")
                f.write("---\n")
                
            print(f"Added publication: {title}")

    except Exception as e:
        print(f"Failed to fetch publications: {e}")

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
