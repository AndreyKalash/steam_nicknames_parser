from configparser import ConfigParser

# чтение конфиг файлов
parser_config = ConfigParser()
parser_config.read(".\\app\\configs\\parser_config.ini")

snp_config = ConfigParser()
snp_config.read(".\\app\\configs\\snp_config.ini")


