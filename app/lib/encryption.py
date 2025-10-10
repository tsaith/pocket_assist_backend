from cryptography.fernet import Fernet

class Encryption:

    def __init__(self, key: str = "0FfChgrS3Xt5IUADFuPAgT-3y0lGLjhNX758PsfQit8="):

        self.key = key
        self.fernet = Fernet(self.key)

    def generate_key(self) -> str:
        return Fernet.generate_key()

    def encrypt(self, password: str) -> str:
        bpassword = password.encode('utf-8')
        return self.fernet.encrypt(bpassword)

    def decrypt(self, encrypted_password: bytes) -> str:
        decrypted = self.fernet.decrypt(encrypted_password)
        return decrypted.decode('utf-8')

    def encrypt_and_decode(self, password: str) -> str:
        encrypted = self.encrypt(password)
        return encrypted.decode('utf-8')

    def encode_and_decrypt(self, encrypted_password: str) -> str:
        bencrypted_password = encrypted_password.encode('utf-8')
        return self.decrypt(bencrypted_password)
