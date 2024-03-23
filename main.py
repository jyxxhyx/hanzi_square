from domain.graph import Graph
from input_handler.reader import read_dict
from model.hanzi_square_model_gurobi import HanziSquareModelGurobi
from output_handler.writer import print_result


def main():
    # 支持迭代计算多轮，生成多个解
    iteration = 1
    # 输入文件
    file_name = 'chaizi/chaizi-jt.txt'
    # file_name = 'chaizi/test.txt'
    # 限制汉字文件（如只能用常用3500字、
    # filter_name = 'chaizi/常用汉字库 3500.txt'
    filter_name = None
    data = read_dict(file_name, filter_file=filter_name)
    graph = Graph(data)
    graph.generate(is_clear_node=False)
    tabu_sols = list()
    for i in range(iteration):
        model = HanziSquareModelGurobi(graph=graph,
                                       time_limit= 8 * 60 * 60,
                                       mip_gap=0.0,
                                       bound=15,
                                       fixed_nodes=set(),
                                       cutoff_sols=tabu_sols)
        x_lst, y_lst = model.solve()
        tabu_sols.append((x_lst, y_lst))
    for (x_lst, y_lst) in tabu_sols:
        print_result(x_lst, y_lst, graph)
    return


if __name__ == '__main__':
    main()
