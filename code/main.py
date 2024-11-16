import random
import re
import copy
import socket
import threading
from multiprocessing import Process, Queue
from threading import Timer, Thread
import time

from typing import List
from input_tree_node import Node
from input_tree import InputTree
from input_tree_mutator import Mutator
from helper_functions import _print_exception, _parse_args
from tqdm import tqdm
from collections import defaultdict


def timed_start(proc: Process, timeout: int):
    Timer(timeout, proc.terminate).start()
    proc.start()


class Fuzzer:

    def __init__(self, verbose, seed, outfilename, seedfile, no_sending):
        self.read_config(args.config)

        self.verbose = verbose
        self.seed = self.expand_seed(seed)
        self.lock = threading.Lock()
        self.outfilename = outfilename
        self.seedfile = seedfile
        self.no_sending = no_sending

    def read_config(self, configfile):
        config_content = open(configfile).read().replace('config.', 'self.')
        exec(config_content)
        if False in [
            item in self.__dict__ 
            for item in [
                "target_urls", 
                "target_host_headers", 
                "grammar", 
                "min_num_mutations", 
                "max_num_mutations", 
                "symbol_mutation_types"
            ]
        ]:
            print("Please make sure that the configuration is complete.")
            exit()

        self.target_hosts = {self.target_urls[i]:self.target_host_headers[i] for i in range(len(self.target_urls))}
 
    def expand_seed(self, seed_string):
        if seed_string == None:
            return None
        expanded_seeds = []
        for seed in seed_string.split(','):
            if '-' in seed:
                start, end = map(int, seed.split('-'))
                expanded_seeds.extend(range(start, end + 1))
            elif seed.isnumeric():
                expanded_seeds.append(int(seed))
        return expanded_seeds

    def send_fuzzy_data(self, inputdata, list_responses):
        try:
            request = inputdata.tree_to_request()
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _socket.connect((inputdata.host, int(inputdata.port)))

            _socket.sendall(request)
            _socket.settimeout(4)

            response = b''
            while True:
                data = _socket.recv(2048)
                if not data:
                    break
                else:
                    response += data

            _socket.shutdown(socket.SHUT_RDWR)
            _socket.close()

            with self.lock:
                list_responses.append(response)
        except socket.timeout:
            with self.lock:
                list_responses.append(b"takes too long")

        except Exception as exception:
            # _print_exception([request])
            # raise exception
            pass

    def get_responses(self, seed, request):
        threads: List[Thread] = []
        list_responses = []
        for target_url in self.target_urls:
            request.seed = seed
            request.url = target_url
            request.host_header = self.target_hosts[target_url]

            request_copy = copy.deepcopy(request)
            thread = threading.Thread(target=self.send_fuzzy_data, args=(request_copy, list_responses))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join(0.5)

        return list_responses

    def blackbox_fuzz_parallel_batch(self):
        for j in range(1): # number of batches
            num_procs = 64
            batch_size = 1000
            seeds_splitted = [[j*batch_size + i for i in list(range(i, batch_size, num_procs))] for i in range(num_procs)]
            quot = Queue()
            processes = [Process(target=self.run, args=(seeds_splitted[i], quot)) for i in range(num_procs)]
            responses_list = []

            for i, proc in enumerate(processes):
                proc.start()

            result = [quot.get() for p in processes]

            for i, proc in enumerate(processes):
                proc.join()

            responses_list = [ent for sublist in result for ent in sublist]

            with open("batch{}.out".format(j), 'w') as outfile:
                outfile.write("\n".join(responses_list))
                outfile.write("\n")

    def blackbox_fuzz_individual(self, filename=None, seeds=None):
        if seeds == None:
            with open(filename, 'r') as _file:
                seeds = [int(line.strip()) for line in _file.readlines()]

        num_procs = 64
        seeds_splitted = [[seeds[i] for i in list(range(i, len(seeds), num_procs))] for i in range(num_procs)]
        quot = Queue()
        processes = [Process(target=self.run_individual, args=(seeds_splitted[i], quot)) for i in range(num_procs)]
        responses_list = []

        for i, proc in enumerate(processes):
            proc.start()

        result = [quot.get() for p in processes]

        for i, proc in enumerate(processes):
            proc.join()

        responses_list = [ent for sublist in result for ent in sublist]

        if self.outfilename is None:
            print("\n".join(responses_list))
            print("\n")
        else:
            with open(self.outfilename, 'w') as outfile:
                outfile.write("\n".join(responses_list))
                outfile.write("\n")

    def run(self, seeds, _queue):
        responses_list = []
        node_score = None

        for seed in seeds:
            base_input = InputTree(self.grammar, seed, "http://hostname/uri", False)
            base_input.build_tree(base_input.root)

            mutator = Mutator(self, base_input, seed, node_score=node_score)
            node_score, mutate_info = mutator.mutate_input()
            if not self.no_sending:
                responses = self.get_responses(seed, base_input)
            else:
                responses = []

            for response in responses:
                if '200 OK'.encode() in response:
                    node_score[mutate_info['node']] += 20
                elif '400 Bad Request'.encode() in response:
                    node_score[mutate_info['node']] += 5
                else:
                    node_score[mutate_info['node']] -= 1 \
                        if node_score[mutate_info['node']] > 0 else 0

            responses_list.append("{} ***** {} ***** {} ***** {}".format(seed, base_input.tree_to_request(), responses, mutator.mutation_messages))

        print('----')
        print(node_score)
        _queue.put(responses_list)
    
    def run_single_thread(self, seeds, scores = None):
        responses_list = []
        return_list = []
        if scores:
            node_score = scores
        else:
            node_score = defaultdict(lambda _: 10)
        is_ok = False

        for seed in seeds:
            base_input = InputTree(self.grammar, seed, "http://hostname/uri", False)
            base_input.build_tree(base_input.root)

            mutator = Mutator(self, base_input, seed, node_score=node_score)
            node_score, mutate_info = mutator.mutate_input()
            if not self.no_sending:
                responses = self.get_responses(seed, base_input)
            else:
                responses = []

            for response in responses:
                if mutate_info:
                    if b'200 OK' in response:
                        node_score[mutate_info['node']] += 20
                        is_ok = True
                    elif b'400 Bad Request' in response:
                        node_score[mutate_info['node']] += 5
                    else:
                        node_score[mutate_info['node']] -= 1 \
                            if node_score[mutate_info['node']] > 0 else 0

            responses_list.append("{} ***** {} ***** {} ***** {}".format(seed, base_input.tree_to_request(), responses, mutator.mutation_messages))
            return_list.append({
                'seed': seed,
                'response': responses,
                'request': base_input.tree_to_request(),
                'message': mutator.mutation_messages,
                'mutate': mutate_info,
                'score': node_score
            })

        # print('----')
        # print(node_score)
        return return_list, responses_list, is_ok
    
    def blackbox_fuzz_batch(self, b_size):
        for j in range(1): # number of batches
            num_procs = 1
            batch_size = b_size
            node_score = None
            responses_list = []

            is_first_ok = True
            first_ok_idx = -1
            resp_oks = 0

            seeds_splitted = [[
                    j * batch_size + i 
                    for i 
                    in list(range(i, batch_size, num_procs))
                ] for i in range(num_procs)
            ]

            for i in tqdm(range(batch_size)):
                ret_vals, resp_vals, is_ok = self.run_single_thread([random.randint(1, 1000)], node_score)
                node_score = ret_vals[-1]['score']
                responses_list.extend(resp_vals)

                if is_ok:
                    if is_first_ok:
                        first_ok_idx = i + 1 
                        is_first_ok = False
                        if i > batch_size // 2:
                            node_score[ret_vals[-1]['mutate']['node']] += batch_size // 2
                    resp_oks += 1

                if i > batch_size // 2:
                    if is_first_ok:
                        for key, val in node_score.items():
                            if val >= 10:
                                node_score[key] = 10

            # responses_list = [ent for sublist in result for ent in sublist]
            print('Scores:', dict(node_score))
            print('Min OK Attempt:', first_ok_idx)
            print('Total OK Responses:', f'{resp_oks}/{batch_size}')

            with open("batch{}.out".format(j), 'w') as outfile:
                outfile.write("\n".join(responses_list))
                outfile.write("\n")

    def run_individual(self, seeds, _queue):
        responses_list = []
        for seed in seeds:
            base_input = InputTree(self.grammar, seed, "http://hostname/uri", False)
            base_input.build_tree(base_input.root)

            mutator = Mutator(self, base_input, seed)
            mutator.mutate_input()
            if not self.no_sending:
                responses = self.get_responses(seed, base_input)
            else:
                responses = []
            responses_list.append("{} ***** {} ***** {} ***** {}".format(seed, base_input.tree_to_request(), responses, mutator.mutation_messages))

        _queue.put(responses_list)

args = _parse_args()
start = time.time()

fuzzer = Fuzzer(args.verbose, args.seed, args.outfilename, args.seedfile, args.no_sending)
if args.individual_mode:
    fuzzer.blackbox_fuzz_individual(fuzzer.seedfile, fuzzer.seed)
else:
    fuzzer.blackbox_fuzz_batch(100)

print('Time cost: ', time.time() - start, 's')
