from typing import Dict, List
from collections import defaultdict, OrderedDict
import re, json
import argparse


REQ = '''POST /rce_json HTTP/1.1
Host: waf:9001
Content-Length: 25
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36
Content-Type: application/json
Accept: */*
Origin: http://waf:9001
Referer: http://waf:9001/
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,vi;q=0.7
Connection: close

{"cmd":"cat /etc/passwd"}'''

BASIC = {
    'config.target_urls': ["http://180.163.83.11:9001/rce_json"],
    'config.target_host_headers': ["180.163.83.11"],
    'config.min_num_mutations': 1,
    'config.max_num_mutations': 1,
    'config.symbol_mutation_types': {'<request-line>': 0, '<space>': 1, '<protocol>': 1, '<separator>': 1, '<version>': 1, '<newline>': 1, '<mime-type-subtype>': 1},
    'config.char_pool': ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\t', '\n', '\x0b', '\x0c', '\r', '\x0e', '\x0f', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d', '\x1e', '\x1f', ' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '[', '\\', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~', '\x7f'],
    'config.symbol_pool': ['(<request-line>, opt(prob=0.9))', '<method-name>', '<space>', '<protocol>', '<separator>', '<version>', '<newline>'],
}


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
            '<method-name><space><request-uri><space><http-version><newline>'
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

    def parse(self, req: str, father: Dict[str, str], self_opt=0.9):
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
                print(base_struct[0])
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

            for k in easy_target:
                easy_target[k] = [
                    item 
                    if item != req_head_and_cont[1] 
                    else f'({req_head_and_cont[1]}, opt(prob={self_opt}))'
                    for item in easy_target[k]
                ]

        easy_target['<body>'] = [with_body[-1].split('\r\n')[0]]
        self.ex_grammar['<request>'][0] += '<newline>'

        if len(easy_target['<body>'][0]) != 0:
            self.ex_grammar['<request>'][0] += '<body>'
        
        host_name = easy_target.get('<host-name>')
        if host_name is not None:
            easy_target['<host-name>'] = ['_HOST_']

        cont_length = easy_target.get('<content-length-value>')
        if cont_length is not None:
            easy_target['<content-length-value>'] = ['_CONTENT_LENGTH_']

        cont_type = easy_target.get("<content-type-value>")
        if cont_type is not None:
            easy_target["<content-type-value>"] = ["<mime-type-subtype>"]

        abs_host = easy_target.get("<absolute-host>")
        if abs_host is not None:
            easy_target["<absolute-host>"] = ["<host-name>"]

        return {**self.ex_grammar, **easy_target}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument("-r", "--req", required=True, help="read from req")
    p.add_argument("-c", "--conf", required=True, help="write to conf")
    args = p.parse_args()

    with open(args.req, "r", encoding='utf-8') as f:
        req = f.read()

    parser = Parser()
    r = parser.fix(req)
    
    father = parser.get_fathers()
    r = parser.parse(r, father)
    to_write = json.dumps(r, indent=4)

    with open(args.conf, "w", encoding='utf-8') as file:
        for k, v in BASIC.items():
            file.write(f'{k} = {v}\n')
        file.write(f'config.grammar = {to_write}')
        
        