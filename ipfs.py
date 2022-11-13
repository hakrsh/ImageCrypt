import nft_storage
from nft_storage.api import nft_storage_api
from pprint import pprint
from cryptography.fernet import Fernet
import requests
import os

configuration = None

if os.path.exists("token"):
    with open("token", "r") as file:
        access_token = file.read()
        configuration = nft_storage.Configuration(access_token = access_token)
else:
    print("Please enter your nft storage API key")
    access_token = input()
    with open("token", "w") as file:
        file.write(access_token)
        configuration = nft_storage.Configuration(access_token = access_token)

class Encryptor():

    def key_create(self):
        key = Fernet.generate_key()
        return key

    def key_write(self, key, key_name):
        with open(key_name, 'wb') as mykey:
            mykey.write(key)

    def key_load(self, key_name):
        with open(key_name, 'rb') as mykey:
            key = mykey.read()
        return key

    def file_encrypt(self, key, original_file, encrypted_file):
        f = Fernet(key)
        with open(original_file, 'rb') as file:
            original = file.read()
        encrypted = f.encrypt(original)
        with open(encrypted_file, 'wb') as file:
            file.write(encrypted)

    def file_decrypt(self, key, encrypted_file, decrypted_file):
        f = Fernet(key)
        with open(encrypted_file, 'rb') as file:
            encrypted = file.read()
        decrypted = f.decrypt(encrypted)
        with open(decrypted_file, 'wb') as file:
            file.write(decrypted)

encryptor=Encryptor()
key = None

def update_index(image, cid):
    try:
        print("trying to update index")
        file = open("index", "rb")
        try:
            encryptor.file_decrypt(key, "index", "index_decrypted")
            with open("index_decrypted", "a") as f:
                f.write(f"{image}:{cid}\n")
            encryptor.file_encrypt(key, "index_decrypted", "index")
            os.remove("index_decrypted")
            return "Index updated successfully"
        except:
            print("Could not decrypt index file")

    except FileNotFoundError:
        with open("plain_index","w") as file:
            file.write(f"{image}:{cid}\n")
        encryptor.file_encrypt(key, "plain_index", "index")
        os.remove("plain_index")
        return "Index created successfully"

def get_cid(image):
    try:
        file = open("index", "rb")
        file.close()
        try:
            encryptor.file_decrypt(key, "index", "index_decrypted")
            # loop through index_decrypted and check if image is there
            with open("index_decrypted", "r") as f:
                for line in f:
                    if image in line:
                        os.remove("index_decrypted")
                        return line.split(":")[1]
            os.remove("index_decrypted")
            return "Image not found"
        except:
            return "Wrong key"
    except FileNotFoundError:
        return "Index not found"

def upload(image):
    if not os.path.exists(image):
        return "File not found"
    image_name = image.split("/")[-1]
    encryptor.file_encrypt(key, image, "encrypted_file")
    # Enter a context with an instance of the API client
    with nft_storage.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = nft_storage_api.NFTStorageAPI(api_client)
        
        body = open('encrypted_file', 'rb')   # path to your image
        try:
            # Store a file
            api_response = api_instance.store(body,_check_return_type=False)
            pprint(api_response)
            cid = api_response.get("value").get("cid")
            print(update_index(image_name, cid))
            os.remove("encrypted_file")
            return "Image uploaded successfully"
        except nft_storage.ApiException as e:
            print("Exception when calling NFTStorageAPI->store: %s\n" % e)
            os.remove("encrypted_file")
            return "Image not uploaded"
        

def download(image):
    cid = get_cid(image)
    if cid == "Image not found" or cid == "Index not found" or cid == "Wrong key":
        return cid
    url  = "https://cloudflare-ipfs.com/ipfs/" + cid
    r = requests.get(url)
    try:
        with open("encrypted_file", "wb") as file:
            file.write(r.content)
        encryptor.file_decrypt(key, "encrypted_file", image)
    except:
        return "Wrong key"
    return "image downloaded successfully" 


if __name__ == '__main__':
    try:
        file = open("key.key", "rb")
        key = encryptor.key_load("key.key")
        file.close()
    except FileNotFoundError:
        key = encryptor.key_create()
        encryptor.key_write(key, "key.key")
    print("Welcome to IPFS image storage")

    while(1):
        print("1. Upload")
        print("2. Download")
        print("3. Exit")
        choice = int(input("Enter your choice: "))
        if choice == 1:
            file = input("Enter the path of the file: ")
            print(upload(file))
        elif choice == 2:
            image = input("Enter the name of the image: ")
            print(download(image))
        elif choice == 3:
            break
        else:
            print("Wrong choice")