import sys
import linecache
import argparse
import random

def _parse_url(url):
    authority = url.split('/')[2]
    uri = '/'.join(url.split('/')[3:])

    if ':' not in authority:
        port = 80
        host = authority
    else:
        host, port = authority.split(':')

    return host, port, authority, uri

def _print_exception(extra_details=[]):
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}, {}'.format(filename, lineno, line.strip(), exc_obj, extra_details))

def _parse_args(): 
    parser = argparse.ArgumentParser(description='T-Reqs: Grammar-based HTTP Fuzzer')

    parser.add_argument('-c', dest="config", required=True, help='config file path')
    parser.add_argument('-i', action="store_true", dest="individual_mode", help="Turns the individual mode on where the fuzzer is run only for specified seeds.")
    parser.add_argument('-n', action="store_true", dest="no_sending", help="Turns the no-sending mode on where the fuzzer only generates the inputs without sending them to the targets.")
    parser.add_argument('-s', dest="seed", help="Only needed for individual mode. Seed parameter for random number generator.")
    parser.add_argument('-v', action="store_true", dest="verbose", help="Only needed for individual mode. Adds verbosity.")
    parser.add_argument('-o', dest="outfilename", help="Only needed for individual mode. File to write output.")
    parser.add_argument('-f', dest="seedfile", help="Only needed for individual mode. Input file containing seeds.")

    args = parser.parse_args()
    return args

def random_choose_with_weights(possible_expansions):
    probabilities = [0]*len(possible_expansions)
    for index, expansion in enumerate(possible_expansions):
        if "prob=" in expansion:
            probability = expansion[expansion.find("prob=")+5:expansion.find(")")]
            probabilities[index] = float(probability)

    probabilities = [(1-sum(probabilities))/probabilities.count(0) if elem == 0 else elem for elem in probabilities]

    chosen_expansion = random.choices(possible_expansions, weights=probabilities)[0]
    # '(<headers-frame-1><data-frame-1>, opts(prob=0.9))'
    # for cases where symbol looks like above, trimming is needed
    if chosen_expansion.startswith('('):
        chosen_expansion = chosen_expansion.split(',')[0][1:]

    return chosen_expansion

def select_node_by_score(score_dict: dict, node_list: dict):
    filtered_nodes = {
        node: score 
        for node, score 
        in score_dict.items() 
        if score > 0 and node in node_list
    }

    if not filtered_nodes:
        return None

    total_score = sum(filtered_nodes.values())
    rand_value = random.uniform(0, total_score)

    cumulative_score = 0
    for node, score in filtered_nodes.items():
        cumulative_score += score
        if rand_value <= cumulative_score:
            return node_list[node]
        
    return None
