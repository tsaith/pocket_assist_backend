import pytest
from cryptography.fernet import Fernet

from app.lib.encryption import Encryption


class TestEncryption:
    """測試 Encryption 類的所有方法"""
    
    def setup_method(self):
        """每個測試方法執行前的設置"""
        self.encryption = Encryption()
        self.test_password = "12345678"
    
    def test_encryption_initialization(self):
        """測試 Encryption 類的初始化"""
        # 測試默認初始化
        encryption = Encryption()
        assert encryption.key is not None
        assert encryption.fernet is not None
        
        # 測試自定義 key 初始化
        custom_key = Fernet.generate_key().decode()
        encryption_custom = Encryption(custom_key)
        assert encryption_custom.key == custom_key
    
    def test_encrypt_and_decrypt(self):
        """測試加密和解密功能 - 使用 encrypt_and_decode() 和 encode_and_decrypt()"""
        # 使用 encrypt_and_decode() 加密得到字串
        encrypted_str = self.encryption.encrypt_and_decode(self.test_password)
        assert isinstance(encrypted_str, str)
        
        # 使用 encode_and_decrypt() 解密得到原本的值
        decrypted_str = self.encryption.encode_and_decrypt(encrypted_str)
        assert isinstance(decrypted_str, str)
        
        # 測試不同長度的密碼
        test_passwords = ["123", "很長的密碼測試"]
        for password in test_passwords:
            encrypted = self.encryption.encrypt_and_decode(password)
            decrypted = self.encryption.encode_and_decrypt(encrypted)
            assert decrypted == password, f"密碼 '{password}' 加密解密失敗"
    
    
if __name__ == "__main__":
    # 運行示例測試
    print("運行示例測試...")
    
    password = "12345678"
    encryption = Encryption()
    
    encrypted = encryption.encrypt(password)
    decrypted = encryption.decrypt(encrypted)
    
    print("password: ", password)
    print("encrypted: ", encrypted)
    print("decrypted: ", decrypted)
    print("type(decrypted): ", type(decrypted))
    
    # 驗證結果
    assert decrypted == password
    print("✅ 示例測試通過！")
