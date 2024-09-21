'''
Description: 
Autor: Yue
Date: 2024-09-20 19:15:35
LastEditors: Yue
LastEditTime: 2024-09-21 11:57:40
'''
import requests

# 定义两个 boundary
boundary1 = "----WebKitFormBoundaryIABEqlYAQTic2F4P"
# boundary2 = "----WebKitFormBoundaryABCDEF"

headers = {
 'Host': '101.91.208.121:9001',
 'Content-Length': '180',
 'Cache-Control': 'max-age=0',
 'Upgrade-Insecure-Requests': '1',
 'Origin': 'http://101.91.208.121:9001',
 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)'
'Chrome/123.0.0.0 Safari/537.36',
 'Accept':
'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/sig'
'ned-exchange;v=b3;q=0.7',
 'Referer': 'http://101.91.208.121:9001/',
 'Accept-Encoding': 'gzip, deflate, br',
 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,vi;q=0.7',
 'Connection': 'close',
 "Content-Type": f"multipart/form-data; boundary={boundary1}"
}


# 构建请求体，手动插入不同的 boundary
data = f"""
--{boundary1}
Content-Disposition: form-data; name="file"; filename="file1.php"
Content-Type: text/php
123
--{boundary1}
Content-Disposition: form-data; name="name"

zhangsan
--{boundary1}
"""

# 设置请求头，使用第一个 boundary 作为起始 boundary
# headers = {
#     "Content-Type": f"multipart/form-data; boundary={boundary1}"
# }

# files = {
# #  'name': ('zhangsan', 'text/plain'),
# #  'email': ('email.txt', '22220@qq.com', 'text/plain'),
#   'file': ('1.php', '123', 'image/jpeg'),
# }
response = requests.post('http://101.91.208.121:9001/upload', headers=headers, data=data, verify=False)
print(response)