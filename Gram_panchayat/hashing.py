import bcrypt

class Hash():
    @staticmethod
    def bcrypt(password: str):
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        return hashed_password.decode('utf-8')
        
    @staticmethod
    def verify(hashed_password, plain_password):
        hashed_bytes = hashed_password.encode('utf-8')
        plain_bytes = plain_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)