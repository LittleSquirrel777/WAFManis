import random
import copy
from collections import defaultdict

from input_tree_node import Node
from helper_functions import _print_exception, random_choose_with_weights,  select_node_by_score

class Mutator:
    mutation_types = {
        0,  # tree mutations
        1   # string mutations
    } 

    def __init__(self, fuzzer, _input, seed=0, reproduce_mode = False, node_score = None):
        self.fuzzer = fuzzer
        self.input = _input
        random.seed(seed)
        self.mutation_messages = []
        self.reproduce_mode = reproduce_mode
        self.node_score = defaultdict(
            lambda: 1, {
                node.symbol: 1
                for node
                in self.input.nonterminal_node_list.values() 
                if node.symbol in self.fuzzer.symbol_mutation_types
            }) if not node_score else node_score

    def mutate_input(self, source_of_mutations = []):
        try:
            if source_of_mutations == []:
                num_mutations = random.randint(self.fuzzer.min_num_mutations, self.fuzzer.max_num_mutations)
                num_done_mutations = 0
                if self.reproduce_mode:
                    self.input_initial_state = copy.deepcopy(self.input)
                    self.mutations = []

                while num_done_mutations < num_mutations:
                    node_to_mutate_pool = [
                        node 
                        for node 
                        in self.input.nonterminal_node_list.values() 
                        if node.symbol in self.fuzzer.symbol_mutation_types
                    ]
                    s_to_n = {
                        node.symbol: node
                        for node
                        in node_to_mutate_pool
                    }
                    if node_to_mutate_pool == []:
                        break

                    # node_to_mutate = random.choice(node_to_mutate_pool)
                    node_to_mutate = select_node_by_score(self.node_score, s_to_n)
                    if not node_to_mutate:
                        node_to_mutate = random.choice(node_to_mutate_pool)
        
                    if self.fuzzer.symbol_mutation_types[node_to_mutate.symbol] == 1: #string mutations
                        mutators = [
                            'remove_random_character',
                            'replace_random_character',
                            'insert_random_character',
                        ]
                    if self.fuzzer.symbol_mutation_types[node_to_mutate.symbol] == 0:
                        mutators = [
                            'remove_random_subtree',
                            'replace_random_subtree',
                            'insert_random_subtree',
                        ]
                        
                    chosen_mutator = random_choose_with_weights(mutators)
                    if self.reproduce_mode:
                        self.mutations.append([chosen_mutator, node_to_mutate, random.getstate()])
                    mutate_info = self.__getattribute__(chosen_mutator)(node_to_mutate, self.fuzzer.verbose)
                
                    num_done_mutations += 1

            else:
                for mutation in source_of_mutations:
                    random.setstate(mutation[2])
                    if mutation[1].id not in self.input.nonterminal_node_list:
                        raise Exception("KeyNotFound: {}".format(mutation[1].id))
                    mutate_info = self.__getattribute__(mutation[0])(self.input.nonterminal_node_list[mutation[1].id], False)

        except Exception as exception: 
            _print_exception() 
            raise(exception)
        
        return self.node_score, mutate_info

    def remove_random_character(self, node, verbose=False):
        s = node.children[0].symbol
        if s:
            pos = random.randint(0, len(s) - 1)
            if verbose:
                print("Removing character {} at pos {} of {}.".format(repr(s[pos]), pos, node.symbol))
            else:
                self.mutation_messages.append("Removing character {} at pos {} of {}.".format(repr(s[pos]), pos, node.symbol)) 

            node.children[0].symbol = s[:pos] + s[pos+1:]
            return {
                'action': 'remove_random_character',
                'modify': {
                    'pos': pos,
                    'data': [s[pos], '']
                },
                'node': node.symbol
            }
        
        return None

    def insert_random_character(self, node, verbose=False):
        s = node.children[0].symbol
        if s:
            pos = random.randint(0, len(s) - 1)
            #random_character = chr(random.randrange(0, 127))
            random_character = random_choose_with_weights(self.fuzzer.char_pool)
            if verbose:
                print("Inserting character {} at pos {} of {}.".format(repr(random_character), pos, node.symbol))
            else:
                self.mutation_messages.append("Inserting character {} at pos {} of {}.".format(repr(random_character), pos, node.symbol))

            node.children[0].symbol = s[:pos] + random_character + s[pos:]
            return {
                'action': 'insert_random_character',
                'modify': {
                    'pos': pos,
                    'data': ['', random_character]
                },
                'node': node.symbol,
            }
        
        return None

    def replace_random_character(self, node, verbose=False):
        s = node.children[0].symbol
        if s:
            pos = random.randint(0, len(s) - 1)
            #random_character = chr(random.randrange(0, 127))
            random_character = random_choose_with_weights(self.fuzzer.char_pool)
            if verbose:
                print("Replacing character {} at pos {} with {} of {}.".format(repr(s[pos]), pos, repr(random_character), repr(node.symbol)))
            else:
                self.mutation_messages.append("Replacing character {} at pos {} with {} of {}.".format(repr(s[pos]), pos, repr(random_character), repr(node.symbol)))

            node.children[0].symbol = s[:pos] + random_character + s[pos+1:]
            return {
                'action': 'replace_random_character',
                'modify': {
                    'pos': pos,
                    'data': [s[pos], random_character]
                },
                'node': node.symbol
            }
        
        return None

    def remove_random_subtree(self, node, verbose=False):
        if node.children:
            pos = random.randint(0, len(node.children) - 1)
            if verbose:
                print("Removing subtree {} under {}.".format(repr(node.children[pos].symbol), repr(node.symbol)))
            else:
                self.mutation_messages.append("Removing subtree {} under {}.".format(repr(node.children[pos].symbol), repr(node.symbol)))

            # Remove the node and its children also from the node list
            old_symbol = node.children[pos].symbol
            self.input.remove_subtree_from_nodelist(node.children[pos])

            node.children = node.children[:pos] + node.children[pos+1:]
            return {
                'action': 'remove_random_subtree',
                'modify': {
                    'pos': pos,
                    'data': [old_symbol, '<null>']
                },
                'node': node.symbol
            }
        
        return None

    def replace_random_subtree(self, node, verbose=False):
        if node.children:
            pos = random.randint(0, len(node.children) - 1)
            # if hasattr(self.fuzzer, 'symbol_pool'):
            #     random_symbol = random_choose_with_weights(self.fuzzer.symbol_pool)
            # else:
            random_symbol = random.choice([_node.symbol for _node in node.children])
            random_subtree = self.input.build_tree(Node(random_symbol))
            if verbose:
                print("Replacing subtree {} under {} with {}.".format(repr(node.children[pos].symbol), repr(node.symbol), repr(random_symbol)))
            else:
                self.mutation_messages.append("Replacing subtree {} under {} with {}.".format(repr(node.children[pos].symbol), repr(node.symbol), repr(random_symbol)))
          
            # Remove the node and its children also from the node list
            old_symbol = node.children[pos].symbol
            self.input.remove_subtree_from_nodelist(node.children[pos])

            node.children = node.children[:pos] + [random_subtree] + node.children[pos+1:]
            return {
                'action': 'replace_random_subtree',
                'modify': {
                    'pos': pos,
                    'data': [old_symbol, random_symbol]
                },
                'node': node.symbol
            }
        
        return None

    def insert_random_subtree(self, node, verbose=False):
        if node.children:
            pos = random.randint(0, len(node.children) - 1)
            # if hasattr(self.fuzzer, 'symbol_pool'):
            #     random_symbol = random_choose_with_weights(self.fuzzer.symbol_pool)
            # else:
            random_symbol = random.choice([_node.symbol for _node in node.children])
            random_subtree = self.input.build_tree(Node(random_symbol))
            if verbose:
                print("Inserting subtree {} at pos {} of {}.".format(repr(random_symbol), pos, repr(node.symbol)))
            else:
                self.mutation_messages.append("Inserting subtree {} at pos {} of {}.".format(repr(random_symbol), pos, repr(node.symbol)))

            node.children = node.children[:pos] + [random_subtree] + node.children[pos:]
            return {
                'action': 'insert_random_subtree',
                'modify': {
                    'pos': pos,
                    'data': ['<null>', random_symbol]
                },
                'node': node.symbol
            }
        
        return None
    
