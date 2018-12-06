import os

class Config():
    log_level =int
    def __init__(self):
        self.log_level =20

class TestConfig(Config):
    def __init__(self):
        super().__init__()
        self.log_level =10
       #self.dbconn = "mssql+pymssql://sa:111@192.168.101.238/mw_weichat?charset=utf8"
       #self.redis_url = 'redis://192.168.101.70:6380/0'

class ProductConfig(Config):
    def __init__(self):
        super().__init__()
        self.log_level =int(os.getenv('LOG_LEVEL',self.log_level))
       #self.dbconn = DatabaseConf(os.getenv('DATABASE_NAME')).sqlalchemy_database_uri()
       #self.redis_url = RedisConfMaster().redis_url()

configs ={
    'test':TestConfig,
    'default':ProductConfig
}

