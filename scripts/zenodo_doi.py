import requests
import json
import os
import zipfile
import sys
import yaml
import re

ZENODO_TOKEN = os.getenv('ZENODO_TOKEN')
# Set ZENODO_ENV=sandbox to use the testing environment
IS_SANDBOX = os.getenv('ZENODO_ENV') == 'sandbox'
URL = 'https://sandbox.zenodo.org/api/deposit/depositions' if IS_SANDBOX else 'https://zenodo.org/api/deposit/depositions'

def get_post_metadata(post_path):
    """Reads the frontmatter of index.md in the post directory."""
    index_file = os.path.join(post_path, 'index.md')
    if not os.path.exists(index_file):
        return None
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.match(r'^---(.*?)---', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1))
    except Exception as e:
        print(f"Error reading metadata: {e}")
    return None

def deposit_post(post_path):
    if not ZENODO_TOKEN:
        print("Error: ZENODO_TOKEN environment variable not set.")
        return None

    metadata = get_post_metadata(post_path)
    title = metadata.get('title', os.path.basename(post_path)) if metadata else os.path.basename(post_path)
    
    print(f"Depositing {post_path} ('{title}') to Zenodo {'(SANDBOX)' if IS_SANDBOX else ''}...")

    # Create zip of post folder
    zip_name = f"{os.path.basename(post_path)}.zip"
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for root, dirs, files in os.walk(post_path):
            for file in files:
                # Include everything in the folder for reproducibility
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, os.path.dirname(post_path))
                zipf.write(abs_path, rel_path)
    
    # 1. Create deposition
    r = requests.post(URL, params={'access_token': ZENODO_TOKEN}, json={}, headers={"Content-Type": "application/json"})
    if r.status_code != 201:
        print(f"Error creating deposition: {r.status_code} {r.text}")
        return None
    
    deposition_id = r.json()['id']
    bucket_url = r.json()['links']['bucket']
    
    # 2. Upload file
    with open(zip_name, 'rb') as fp:
        r = requests.put(f"{bucket_url}/{zip_name}", data=fp, params={'access_token': ZENODO_TOKEN})
    
    if r.status_code != 201:
        print(f"Error uploading file: {r.status_code} {r.text}")
        return None
    
    # 3. Update Metadata
    zenodo_metadata = {
        'metadata': {
            'title': f"Research Data and Code: {title}",
            'upload_type': 'software', # Better for code/scripts
            'description': f"Automated deposit for the blog post: {title}. Includes all associated scripts, data, and plots for reproducibility.",
            'creators': [{'name': 'Hall, Michael B.', 'orcid': '0000-0003-3683-6208'}]
        }
    }
    r = requests.put(f"{URL}/{deposition_id}", params={'access_token': ZENODO_TOKEN}, data=json.dumps(zenodo_metadata), headers={"Content-Type": "application/json"})
    
    if r.status_code != 200:
        print(f"Error updating metadata: {r.status_code} {r.text}")
        return None
    
    # 4. Publish
    r = requests.post(f"{URL}/{deposition_id}/actions/publish", params={'access_token': ZENODO_TOKEN})
    if r.status_code != 202:
        print(f"Error publishing: {r.status_code} {r.text}")
        return None
    
    doi = r.json().get('metadata', {}).get('doi')
    print(f"Success! Published DOI: {doi}")
    
    # Cleanup zip
    os.remove(zip_name)
    return doi

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python zenodo_doi.py <post_path>")
        sys.exit(1)
    
    doi = deposit_post(sys.argv[1])
    if doi:
        # Output DOI for the GitHub Action to catch
        print(f"RESULT_DOI={doi}")
