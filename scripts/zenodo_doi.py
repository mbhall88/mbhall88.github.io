import requests
import json
import os
import zipfile
import sys

ZENODO_TOKEN = os.getenv('ZENODO_TOKEN')
ACCESS_TOKEN = ZENODO_TOKEN
URL = 'https://zenodo.org/api/deposit/depositions'

def deposit_post(post_path):
    print(f"Depositing {post_path} to Zenodo...")
    # Create zip of post folder
    zip_name = f"{os.path.basename(post_path)}.zip"
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for root, dirs, files in os.walk(post_path):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(post_path, '..')))
    
    # Create deposition
    r = requests.post(URL, params={'access_token': ACCESS_TOKEN}, json={}, headers={"Content-Type": "application/json"})
    if r.status_code != 201:
        print(f"Error creating deposition: {r.status_code} {r.text}")
        return None
    
    deposition_id = r.json()['id']
    bucket_url = r.json()['links']['bucket']
    
    # Upload file
    with open(zip_name, 'rb') as fp:
        r = requests.put(f"{bucket_url}/{zip_name}", data=fp, params={'access_token': ACCESS_TOKEN})
    
    if r.status_code != 201:
        print(f"Error uploading file: {r.status_code} {r.text}")
        return None
    
    # Metadata
    # This should be more robust
    metadata = {
        'metadata': {
            'title': f"Blog post: {os.path.basename(post_path)}",
            'upload_type': 'publication',
            'publication_type': 'other',
            'description': 'Automatic deposit from blog overhaul.',
            'creators': [{'name': 'Hall, Michael B.', 'orcid': '0000-0003-3683-6208'}]
        }
    }
    r = requests.put(f"{URL}/{deposition_id}", params={'access_token': ACCESS_TOKEN}, data=json.dumps(metadata), headers={"Content-Type": "application/json"})
    
    if r.status_code != 200:
        print(f"Error updating metadata: {r.status_code} {r.text}")
        return None
    
    # Publish (uncomment only when ready)
    # r = requests.post(f"{URL}/{deposition_id}/actions/publish", params={'access_token': ACCESS_TOKEN})
    # if r.status_code != 202:
    #     print(f"Error publishing: {r.status_code} {r.text}")
    #     return None
    
    doi = r.json().get('metadata', {}).get('prereserve_doi', {}).get('doi')
    print(f"Success! Prereserved DOI: {doi}")
    return doi

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python zenodo_doi.py <post_path>")
        sys.exit(1)
    deposit_post(sys.argv[1])
