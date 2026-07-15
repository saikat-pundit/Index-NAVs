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
    
    if not cookie_value:
        print("❌ No cookie value provided")
        return
    
    # Get public key from GitHub
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get public key: {response.text}")
        return
    
    public_key_data = response.json()
    
    # GitHub returns the key in base64 format, not PEM
    # Convert base64 to proper PEM format
    key_bytes = base64.b64decode(public_key_data['key'])
    
    # Load the public key from bytes (it's in DER format, not PEM)
    try:
        public_key = serialization.load_der_public_key(key_bytes)
    except Exception as e:
        print(f"❌ Failed to load public key: {e}")
        return
    
    # Encrypt the cookie using RSA OAEP
    encrypted = public_key.encrypt(
        cookie_value.encode('utf-8'),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    encrypted_value = base64.b64encode(encrypted).decode('utf-8')
    
    # Update the secret
    url = f"https://api.github.com/repos/{repo}/actions/secrets/SENSIBULL_COOKIE"
    data = {
        "encrypted_value": encrypted_value,
        "key_id": public_key_data['key_id']
    }
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [201, 204]:
        print("✅ Secret updated successfully")
    else:
        print(f"❌ Failed to update secret: {response.status_code} - {response.text}")

if __name__ == "__main__":
    update_github_secret()
