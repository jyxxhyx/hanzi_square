

def print_result(x_lst, y_lst, graph):
    header = '\t'
    for node in x_lst:
        header += f'{node}\t'
    print(header)
    for node_y in y_lst:
        row = f'{node_y}\t'
        for node_x in x_lst:
            row += f'{graph.arcs[node_x, node_y]}\t'
        print(row)