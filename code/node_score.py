import random


score_dict = {
    'node1': 10,
    'node2': 5,
    'node3': 0,  
    'node4': 15
}


def select_node_by_score(score_dict: dict):
    filtered_nodes = {
        node: score 
        for node, score 
        in score_dict.items() 
        if score > 0
    }

    if not filtered_nodes:
        return None

    total_score = sum(filtered_nodes.values())
    rand_value = random.uniform(0, total_score)

    cumulative_score = 0
    for node, score in filtered_nodes.items():
        cumulative_score += score
        if rand_value <= cumulative_score:
            return node

selected_node = select_node_by_score(score_dict)
print(f"Selected node: {selected_node}")

