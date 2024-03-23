

def read_dict(file, filter_file: str = None):
    """
    Read file
    :param file: file of strokes and characters
    :param filter_file: restricted set of files
    :return:
    """
    # TODO to support the format of IDS

    data = {}
    char_filter = None
    if filter_file is not None:
        with open(filter_file, 'r') as f:
            line = f.readline().strip()
            char_filter = set(line)

    with open(file, 'rt') as fd:
        for line in fd:
            item_list = line.strip().split('\t')
            key = item_list[0]
            value = [i.strip().split() for i in item_list[1:]]
            # 只保留拆成2部分的
            value = [item for item in value if len(item) == 2]
            # value为空的不存，多种拆字只保留一个
            if not value:
                continue
            if char_filter is not None and key in char_filter:
                # 有多种拆字方法的，只读取第一个
                data[key] = [value[0]]
    return data
