import yaml
from collections import OrderedDict

class OrderDictEx(OrderedDict):
    pass

def orderdictex_representer(dumper, data):
    from yaml.nodes import MappingNode,ScalarNode
    items = [(key,value) for key, value in data.items()]
    value = []
    node = MappingNode('tag:yaml.org,2002:map', value, flow_style=dumper.default_flow_style)

    best_style = True

    for item_key, item_value in items:
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)
        if not (isinstance(node_key, ScalarNode) and not node_key.style):
            best_style = False
        if not (isinstance(node_value, ScalarNode) and not node_value.style):
            best_style = False
        value.append((node_key, node_value))
    if node.flow_style is None:
        if dumper.default_flow_style is not None:
            node.flow_style = dumper.default_flow_style
        else:
            node.flow_style = best_style
    return node

yaml.add_representer(OrderDictEx, orderdictex_representer)