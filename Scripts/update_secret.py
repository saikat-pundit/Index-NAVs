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

    # 1. Get the public key from GitHub
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Failed to get public key: {resp.text}")
        return
    
    key_data = resp.json()
    key_base64 = key_data['key']          # This is a base64 string
    key_id = key_data['key_id']
    
    # 2. Decode from base64 (this gives us the raw key bytes)
    key_bytes = base64.b64decode(key_base64)
    
    # 3. Try to load the key – first as DER, then as PEM
    public_key = None
    error_messages = []
    
    # Attempt 1: DER format
    try:
        public_key = serialization.load_der_public_key(key_bytes)
        print("✅ Loaded key as DER")
    except Exception as e:
        error_messages.append(f"DER failed: {e}")
        
        # Attempt 2: PEM format (raw bytes might be the PEM string)
        try:
            public_key = serialization.load_pem_public_key(key_bytes)
            print("✅ Loaded key as PEM (raw bytes)")
        except Exception as e2:
            error_messages.append(f"PEM (raw bytes) failed: {e2}")
            
            # Attempt 3: Maybe the key_bytes are already a PEM string without headers?
            # Try to decode to text and add headers if missing
            try:
                pem_str = key_bytes.decode('utf-8').strip()
                if not pem_str.startswith("-----BEGIN PUBLIC KEY-----"):
                    pem_str = "-----BEGIN PUBLIC KEY-----\n" + pem_str + "\n-----END PUBLIC KEY-----"
                public_key = serialization.load_pem_public_key(pem_str.encode('utf-8'))
                print("✅ Loaded key as PEM with added headers")
            except Exception as e3:
                error_messages.append(f"PEM with headers failed: {e3}")
                print("❌ All attempts to load public key failed:")
                for msg in error_messages:
                    print(f"  {msg}")
                return
    
    if public_key is None:
        return

    # 4. Encrypt the cookie using RSA OAEP
    try:
        encrypted = public_key.encrypt(
            cookie_value.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        encrypted_value = base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"❌ Encryption failed: {e}")
        return

    # 5. Update the secret
    update_url = f"https://api.github.com/repos/{repo}/actions/secrets/SENSIBULL_COOKIE"
    payload = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    resp = requests.put(update_url, headers=headers, json=payload)
    
    if resp.status_code in (201, 204):
        print("✅ Secret updated successfully")
    else:
        print(f"❌ Failed to update secret: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    update_github_secret()
