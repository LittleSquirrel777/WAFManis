from typing import Dict, List
from collections import defaultdict, OrderedDict
import re, json


REQ = '''POST /sqli_post HTTP/1.1
Host: waf:9002
Content-Length: 64
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
Origin: http://waf:9002
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Referer: http://waf:9002/
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,vi;q=0.7
Connection: close

id=1+UNION+SELECT+null%2C+password+FROM+users+WHERE+id+%3D+1+--+
'''


def split_comm(gram_str: str) -> List[str]:
    elements = re.findall(r'<[^>]+>', gram_str)
    return elements


class Parser:
    def __init__(self, base_gram_path='conf/base_grammar.conf'):
        self.ex_grammar = defaultdict(list)
        self.base_grammar = {}
        self.init_ex_gram()
        self.get_base_grammar(base_gram_path)

    def init_ex_gram(self):
        self.ex_grammar['<start>'] = ['<request>']
        # self.ex_grammar['<request>'] = [
        #     '<method-name><request-uri><http-version><base><entity-size-header><some-header><some-header><body>'
        # ]
        self.ex_grammar['<request>'] = [
            '<method-name><request-uri><http-version>'
        ]

        self.ex_grammar['<space>'] = [' ']
        self.ex_grammar['<colon>'] = [':']
        self.ex_grammar['<newline>'] = ['\r\n']
        # self.ex_grammar['<base>'] = ['<host><connection>']
        # self.ex_grammar['<entity-size-header>'] = ['<content-length>']

    def get_base_grammar(self, base_gram_path: str):
        with open(base_gram_path, 'r', encoding='utf-8') as f:
            grammar = f.read().replace('config.grammar', 'self.base_grammar')
            exec(grammar)

    def fix(self, req: str):
        return req.replace('\n', '\r\n')
    
    def get_fathers(self):
        father = {}
        grammar = self.base_grammar

        for key, val in grammar.items():
            for it in val:
                if it.startswith('<') and it.endswith('>'):
                    comms = split_comm(it)
                    for comm in comms:
                        father[comm] = key
                else:
                    father[it] = key
        return father
    
    def expand_grammar(self, key: str):
        result = {}

        def recursive_extract(current_key):
            if current_key in self.base_grammar:
                for production in self.base_grammar[current_key]:
                    result[current_key] = list(set(result.get(current_key, []) + [production]))
                    
                    sub_items = split_comm(production)
                    for sub_item in sub_items:
                        if sub_item not in result:
                            result[sub_item] = []
                        recursive_extract(sub_item)

        recursive_extract(key)
        return result

    def parse(self, req: str, father: Dict[str, str]):
        easy_target = OrderedDict()
        with_body = req.split('\r\n\r\n')

        without_body = with_body[0]
        req_lines = without_body.split('\r\n')

        for req_line in req_lines:
            req_head_and_cont = req_line.split(': ')
            if len(req_head_and_cont) == 1:
                req_msg = req_head_and_cont[0].split(' ')
                easy_target['<method-name>'] = [req_msg[0]]
                easy_target['<request-uri>'] = [req_msg[1]]
                easy_target['<http-version>'] = [req_msg[2]]
                continue
            
            key_name = req_head_and_cont[0]
            key = f"<{key_name.lower()}>"
            self.ex_grammar['<request>'][0] += key

            real_cont_name = f'<{key_name.lower()}-content>'
            base_struct = self.base_grammar.get(key)
            if base_struct is not None:
                real_cont_name = split_comm(base_struct[0])[-2]

            easy_target[key] = [f'<{key_name.lower()}-header-name><colon><space>{real_cont_name}<newline>']
            easy_target[f'<{key_name.lower()}-header-name>'] = [key_name]
            
            key_father = father.get(req_head_and_cont[1])
            print(req_head_and_cont[1])
            if key_father is not None:
                easy_target[f'{real_cont_name}'] = [key_father]
                easy_target[key_father] = self.base_grammar[key_father]
            else:
                easy_target[f'{real_cont_name}'] = [req_head_and_cont[1]]

            key_sons = self.base_grammar.get(real_cont_name)
            if key_sons is not None:
                subdict = self.expand_grammar(real_cont_name)
                easy_target = {**easy_target, **subdict}

        easy_target['<body>'] = [with_body[-1].split('\r\n')[0]]
        return {**self.ex_grammar, **easy_target}


if __name__ == '__main__':
    parser = Parser()
    r = parser.fix(REQ)
    
    father = parser.get_fathers()
    # print(father.get('application/x-www-form-urlencoded'))

    r = parser.parse(r, father)
    with open('./ex_grammar.json', 'w', encoding='utf-8') as f:
        json.dump(r, f, indent=4)