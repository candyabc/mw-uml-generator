import os

class Config():
    port =int
    log_level =int
    def __init__(self):
        self.port = 8080
        self.log_level =20
        self.myaddress = 'localhost'


class TestConfig(Config):
    def __init__(self):
        super().__init__()
        self.log_level =10


class ProductConfig(Config):
    def __init__(self):
        super().__init__()
        self.port =int(os.getenv('WEB_PORT',self.port))
        self.log_level =int(os.getenv('LOG_LEVEL',self.log_level))

configs ={
    'test':TestConfig,
    'default':ProductConfig
}

