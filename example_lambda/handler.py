import requests, boto3, threading, socket, random, uuid, tempfile
from datetime import datetime
# Bad patterns at import time
r = requests.get("https://example.com")  # PY002
s3 = boto3.client("s3")                  # PY006
bg = threading.Thread(target=lambda: None)  # PY003
bg.start()  # PY003
sock = socket.socket()                   # PY004
seed = random.random()                   # PY005
uid = uuid.uuid4()                       # PY005
now = datetime.now()                     # PY005
tmp = tempfile.NamedTemporaryFile()      # PY007
DATA = []                                # PY001

def handler(event, context):
    return {"statusCode": 200, "body": "ok"}