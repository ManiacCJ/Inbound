from Inbound.settings import BASE_DIR
import os

print(BASE_DIR)
aa = os.path.join(BASE_DIR, 'db.sqlite3')
print(aa)