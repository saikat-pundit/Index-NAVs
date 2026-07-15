import os
import requests
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

def update_github_secret():
    token = os.environ['GH_PAT']
    repo = os.environ['GITHUB_REPOSITORY']
    cookie_value = os.environ['COOKIE_VALUE']
    
    # Get public key
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    public_key_data = response.json()
    
    # Encrypt using public key
    public_key = serialization.load_pem_public_key(
        public_key_data['key'].encode()
    )
    encrypted = public_key.encrypt(
        cookie_value.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    encrypted_value = base64.b64encode(encrypted).decode()
    
    # Update secret
    url = f"https://api.github.com/repos/{repo}/actions/secrets/SENSIBULL_COOKIE"
    data = {
        "encrypted_value": encrypted_value,
        "key_id": public_key_data['key_id']
    }
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code == 201 or response.status_code == 204:
        print("✅ Secret updated successfully")
    else:
        print(f"❌ Failed to update secret: {response.text}")

if __name__ == "__main__":
    update_github_secret()
