import re
import argparse
from pathlib import Path
import sys
import graphviz as gv
import copy


class CDPParser:
    def __init__(self):
        self.links = dict()

    def parse_and_append(self, file_path):
        local_device = None
        with open(file_path, 'r') as file:
            lines = file.readlines()
        for line in lines:
            if "show cdp neighbors" in line:
                local_device = line.split(">")[0].strip()
                break
        pattern = re.compile(r'(\S+)\s+(\S+ \S+)\s+\d+\s+[\S ]+\s+\S+\s+(\S+ \S+[\d/]+)')
        for line in lines:
            match = pattern.match(line)
            if match:
                remote_device = match.group(1)
                local_interface = match.group(2)
                remote_interface = match.group(3)
                self.links[(local_device, local_interface)] = (remote_device, remote_interface)

    def make_unique(self):
        unique_links = {}
        seen_links = set()
        for local, remote in self.links.items():
            link = frozenset((local, remote))
            if link not in seen_links:
                seen_links.add(link)
                unique_links[local] = remote
        self.links = unique_links

    def print(self):
        for key, value in self.links.items():
            print(key, value)

    def get_copy(self):
        return copy.deepcopy(self.links)


gv_styles = {"graph": {"label": "Network Map",
                       "fontsize": "16",
                       "fontcolor": "white",
                       "bgcolor": "#3F3F3F",
                       "rankdir": "BT"},
             "nodes": {"fontname": "Helvetica",
                       "shape": "box",
                       "fontcolor": "white",
                       "color": "#006699",
                       "style": "filled",
                       "fillcolor": "#006699",
                       "margin": "0.4"},
             "edges": {"style": "dashed",
                       "color": "green",
                       "arrowhead": "open",
                       "fontname": "Courier",
                       "fontsize": "14",
                       "fontcolor": "white"}}


def apply_gv_styles(graph, styles):
    graph.graph_attr.update(("graph" in styles and styles["graph"]) or {})
    graph.node_attr.update(("nodes" in styles and styles["nodes"]) or {})
    graph.edge_attr.update(("edges" in styles and styles["edges"]) or {})
    return graph


def draw_topology(topology_dict, out_filename="img/topology", style_dict=gv_styles) -> None:
    nodes = set([item[0] for item in list(topology_dict.keys()) + list(topology_dict.values())])

    graph = gv.Graph(format="svg")

    for node in nodes:
        graph.node(node)

    for key, value in topology_dict.items():
        head, t_label = key
        tail, h_label = value
        graph.edge(head, tail, headlabel=h_label, taillabel=t_label, label=" " * 12)

    graph = apply_gv_styles(graph, style_dict)
    filename = graph.render(filename=out_filename)
    print("Topology saved in", filename)


def main():
    parser = argparse.ArgumentParser(description="Программа для вывода имен файлов из заданной директории.")
    parser.add_argument('-s', '--source-directory', default='./cdp',
                        help="Путь к исходной директории (по умолчанию: ./cdp)")
    args = parser.parse_args()

    source_directory = Path(args.source_directory)

    if not source_directory.exists():
        print(f"Указанная директория {source_directory} не существует.")
        sys.exit(1)

    parser = CDPParser()

    for filename in source_directory.iterdir():
        if filename.is_file():
            parser.parse_and_append(filename)

    # parser.dump()
    parser.make_unique()
    # print('-'*100)
    # parser.dump()
    draw_topology(parser.get_copy())


if __name__ == "__main__":
    main()
