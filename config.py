data_file = open('security.txt', mode='rt', encoding='utf-8')
TOKEN = data_file.readline().strip()
post_login = data_file.readline().strip()
post_password = data_file.readline().strip()
