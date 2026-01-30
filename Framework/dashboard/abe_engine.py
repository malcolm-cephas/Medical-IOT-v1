import json
import base64
import os
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

class ABEEngine:
    def __init__(self):
        self.master_key_pair = None
        self.public_key = None
        
        # In a real system, these would be loaded from secure storage
        # For this simulation, we'll generate them if they don't exist in memory
        # or load from a file if we want persistence
        self.key_file = "abe_master.pem"
        self._load_or_generate_keys()

    def _load_or_generate_keys(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                self.master_key_pair = RSA.import_key(f.read())
                self.public_key = self.master_key_pair.publickey()
        else:
            self.setup()

    def setup(self):
        """
        Initialize the Authority. Generate Master Key Pair.
        """
        self.master_key_pair = RSA.generate(2048)
        self.public_key = self.master_key_pair.publickey()
        
        # Save to file for persistence across restarts
        with open(self.key_file, 'wb') as f:
            f.write(self.master_key_pair.export_key())
            
        return "Setup Complete. Master Key Generated."

    def keygen(self, username, attributes):
        """
        Generate a 'User Key' for a specific user.
        The User Key contains the list of attributes, SIGNED by the Master Key.
        This prevents the user from lying about their attributes.
        """
        if not self.master_key_pair:
            raise Exception("System not setup")

        # Create a payload of the user's attributes
        user_data = {
            "username": username,
            "attributes": sorted(attributes) # Sort to ensure consistent hashing
        }
        user_data_json = json.dumps(user_data).encode('utf-8')
        
        # Sign the attributes
        h = SHA256.new(user_data_json)
        signature = pkcs1_15.new(self.master_key_pair).sign(h)
        
        # The "User Key" is the data + the signature
        user_key = {
            "data": user_data,
            "signature": base64.b64encode(signature).decode('utf-8')
        }
        
        return user_key

    def encrypt(self, message, policy_attributes):
        """
        Encrypts a message such that it can only be decrypted by a user
        who possesses ALL the attributes in `policy_attributes`.
        
        Mechanism:
        1. Encrypt message with a random AES Key.
        2. Encrypt the AES Key itself?
        
        Wait, in a strict simulation without ABE math, we can't mathematically enforce the policy 
        on the client side without the server.
        
        Hybrid Approach for Simulation:
        - We encrypt the data with AES.
        - We act as the "Cloud Provider" who stores the data.
        - When a user requests to decrypt, they MUST provide their Signed Attributes.
        - The Engine verifies the signature (Authentication).
        - The Engine checks if attributes match policy (Authorization).
        - If OK, the Engine returns the AES key (or decrypts for them).
        
        To make it look like ABE:
        Input: Data, Policy
        Output: Ciphertext (contains {AES_Encrypted_Data, Policy})
        """
        
        # 1. Generate AES Key and Nonce
        aes_key = get_random_bytes(16)
        cipher_aes = AES.new(aes_key, AES.MODE_EAX)
        ciphertext, tag = cipher_aes.encrypt_and_digest(message.encode('utf-8'))
        
        # 2. Prepare the 'Ciphertext' package
        # In a real ABE, the aes_key would be encrypted using the attributes.
        # Here, we will encrypt the aes_key using the Master Public Key so only the Authority (us) can recover it
        # to perform the policy check during decryption phase.
        
        cipher_rsa = PKCS1_OAEP.new(self.public_key)
        enc_aes_key = cipher_rsa.encrypt(aes_key)
        
        package = {
            "policy": sorted(policy_attributes),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
            "nonce": base64.b64encode(cipher_aes.nonce).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8'),
            "encrypted_key": base64.b64encode(enc_aes_key).decode('utf-8')
        }
        
        return package

    def decrypt(self, ciphertext_package, user_key):
        """
        Decrypts the package if the user_key's attributes satisfy the policy.
        """
        # 1. Verify User Key Signature
        user_data = user_key['data']
        signature = base64.b64decode(user_key['signature'])
        
        user_data_json = json.dumps(user_data).encode('utf-8')
        h = SHA256.new(user_data_json)
        
        try:
            pkcs1_15.new(self.public_key).verify(h, signature)
        except (ValueError, TypeError):
            raise Exception("Invalid User Key: Signature Verification Failed.")
            
        # 2. Check Policy
        # AND Policy: User must have ALL attributes in the policy
        policy = ciphertext_package.get('policy', [])
        user_attrs = set(user_data['attributes'])
        
        for req_attr in policy:
            if req_attr not in user_attrs:
                raise Exception(f"Access Denied: Missing attribute '{req_attr}'")
                
        # 3. Decrypt
        # Recover AES Key (Authority does this part)
        enc_aes_key = base64.b64decode(ciphertext_package['encrypted_key'])
        cipher_rsa = PKCS1_OAEP.new(self.master_key_pair)
        aes_key = cipher_rsa.decrypt(enc_aes_key)
        
        # Decrypt Data
        nonce = base64.b64decode(ciphertext_package['nonce'])
        tag = base64.b64decode(ciphertext_package['tag'])
        ciphertext = base64.b64decode(ciphertext_package['ciphertext'])
        
        cipher_aes = AES.new(aes_key, AES.MODE_EAX, nonce)
        data = cipher_aes.decrypt_and_verify(ciphertext, tag)
        
        return data.decode('utf-8')

# Singleton instance
abe = ABEEngine()
