import pymysql

# Заставляем Django думать что у нас нужная версия
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()