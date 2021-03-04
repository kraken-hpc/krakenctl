from rich.console import Console
from rich.table import Column, Table
from rich.text import Text
from rich.style import Style
from typing import List
from functools import cmp_to_key
import yaml


# # r = requests.get('http://192.168.57.10:3141/cfg/nodes')
# # json = r.json()

# # print(json)

# columns = []

# for node in json["nodes"]:
#     # print(node.keys())
#     for key in node.keys():
#         if key not in columns:
#             columns.append(key)

# console = Console()

# table = Table(show_header=True, header_style="bold magenta")
# for key in columns:
#     table.add_column(key)

# # table.add_row("blah", "blah")

# for node in json["nodes"]:
#     row_strings = []
#     for key in columns:
#         if key in node.keys():
#             row_strings.append(str(node[key]))
#         else:
#             row_strings.append("")
#     table.add_row(*row_strings)
# # node[key]
# # table.add_column("Date", style="dim", width=12)
# # table.add_column("Title")
# # table.add_column("Production Budget", justify="right")
# # table.add_column("Box Office", justify="right")
# # table.add_row(
# #     "Dev 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,0000", "$375,126,118"
# # )
# # table.add_row(
# #     "May 25, 2018",
# #     "[red]Solo[/red]: A Star Wars Story",
# #     "$275,000,0000",
# #     "$393,151,347",
# # )
# # table.add_row(
# #     "Dec 15, 2017",
# #     "Star Wars Ep. VIII: The Last Jedi",
# #     "$262,000,000",
# #     "[bold]$1,332,539,889[/bold]",
# # )

# console.print(table)


def print_table(nodes: List[dict], verbose: bool = False):
    columns = []

    for node in nodes:
        # print(node.keys())
        for key in node.keys():
            if key not in columns:
                columns.append(key)

    columns.sort(key=column_sort)

    console = Console()

    table = Table(show_header=True,
                  header_style="bold magenta", show_lines=True)
    for key in columns:
        table.add_column(key)

    # table.add_row("blah", "blah")

    nodes.sort(key=node_sort)

    for node in nodes:
        row_strings = []
        for key in columns:
            if key in node.keys():
                if verbose:
                    row_strings.append(parse_item_long(node[key]))
                else:
                    row_strings.append(parse_item_short(node[key]))
                # text = yaml.dump(
                #     node[key], default_style=None, sort_keys=False)
                # # print("[{}]".format(text))
                # if text.endswith('...\n'):
                #     text = text[:-4]
                # if text.endswith('\n'):
                #     text = text[:-1]
                # row_strings.append(text)
                # if type(node[key]) == list:
                #     row_strings.append(list_to_string(node[key], 0))
                # elif type(node[key]) == dict:
                #     row_strings.append(dict_to_string(node[key], 0))
                # else:
                #     row_strings.append(str(node[key]))
            else:
                row_strings.append("")
        table.add_row(*row_strings)

    console.print(table, no_wrap=True)


def parse_item_short_dict(provided_dict: dict) -> List[Text]:
    final_lines = []
    state = provided_dict.get("state")
    item_id = provided_dict.get("id")
    item_type = provided_dict.get("@type")
    first_key = list(provided_dict.keys())[0]
    content_key = ""
    content = ""
    final_content = ""
    if item_id is not None:
        content_key = "id"
        content = item_id
    elif item_type is not None:
        content_key = "@type"
        content = item_type
    else:
        content_key = first_key
        content = item[first_key]

    final_content = Text("- ", style="bold")
    final_content.append(content_key, style="bold")
    final_content.append(": ", style="bold")
    final_content.append(content, style=Style(bold=False))
    final_lines.append(final_content)

    if state is not None:
        state_content = Text("  ")
        state_content.append("state", style="bold")
        state_content.append(": ", style="bold")
        state_content.append(color_state(state))
        final_lines.append(state_content)

    return final_lines


def parse_item_short_list(provided_list: list) -> List[Text]:
    final_lines = []
    for item in provided_list:
        if type(item) == dict:
            dict_lines = parse_item_short_dict(item)
            final_lines.extend(dict_lines)

    return final_lines


def parse_item_short(provided_item) -> Text:
    final_string = None
    if type(provided_item) == list:
        list_lines = parse_item_short_list(provided_item)
        final_string = Text("\n").join(list_lines)
    elif type(provided_item) == dict:
        dict_lines = parse_item_short_dict(provided_item)
        final_string = "\n".join(dict_lines)
    else:
        final_string = Text(str(provided_item))

    return final_string


def parse_item_long(items_list) -> str:
    final_string = yaml.dump(
        items_list, default_style=None, sort_keys=False)
    # print("[{}]".format(text))
    if final_string.endswith('...\n'):
        final_string = final_string[:-4]
    if final_string.endswith('\n'):
        final_string = final_string[:-1]

    return final_string


# def add_to_string(current_string: str, addition: str) -> str:
#     if current_string == "":
#         return addition
#     else:
#         return "{}\n{}".format(current_string, addition)


# def dict_to_string_old(item_dict: dict, tab_level: int) -> str:
#     final_string = ""
#     for item in item_dict.items():
#         if type(item[1]) == list:
#             final_string = add_to_string(
#                 final_string, "{:{width}}{}:\n{}".format("", item[0],  list_to_string(item[1], tab_level + 1), width=tab_level*2))
#         elif type(item[1]) == dict:
#             final_string = add_to_string(
#                 final_string, "{:{width}}{}:\n{}".format("", item[0], dict_to_string(item[1], tab_level + 1), width=tab_level*2))
#         else:
#             final_string = add_to_string(
#                 final_string, "{:{width}}{}:{}".format("", item[0], str(item[1]), width=tab_level*2))
#     return final_string


# def list_to_string(item_list: list, tab_level: int) -> str:
#     print(tab_level)
#     final_string = ""
#     for item in item_list:
#         if type(item) == dict:
#             final_string = add_to_string(
#                 final_string, "{:>{width}}{}".format("-", dict_to_string(item, tab_level + 1), width=tab_level * 2))
#         elif type(item) == list:
#             final_string = add_to_string(
#                 final_string, "{:>{width}}{}".format("-", list_to_string(item, tab_level + 1), width=tab_level * 2))
#         else:
#             final_string = add_to_string(
#                 final_string, "{:>{width}}{}".format("-", str(item), width=tab_level * 2))
#     return final_string

special_keys = ["nodename", "id"]


def column_cmp(a, b):
    if a in special_keys and b not in special_keys:
        return -1
    elif a not in special_keys and b in special_keys:
        return 1
    elif a in special_keys and b in special_keys:
        if special_keys.index(a) > special_keys.index(b):
            return 1
        elif special_keys.index(a) < special_keys.index(b):
            return -1
        elif special_keys.index(a) == special_keys.index(b):
            return 0
    elif a > b:
        return 1
    elif a < b:
        return -1
    else:
        return 0

    # if a[1] > b[1]:
    #     return -1
    # elif a[1] == b[1]:
    #     if a[0] > b[0]:
    #         return 1
    #     else:
    #         return -1
    # else:
    #     return 1


column_sort = cmp_to_key(column_cmp)


def node_cmp(a: dict, b: dict):
    a_parent_id = a.get("parentId")
    if a_parent_id is None or a_parent_id == "":
        return -1
    b_parent_id = b.get("parentId")
    if b_parent_id is None or b_parent_id == "":
        return 1
    a_nodename = a.get("nodename")
    b_nodename = b.get("nodename")
    if a_nodename is None and b_nodename is not None:
        return -1
    elif a_nodename is not None and b_nodename is None:
        return 1
    elif a_nodename is None and b_nodename is None:
        return 0
    elif a_nodename > b_nodename:
        return 1
    elif a_nodename < b_nodename:
        return -1
    else:
        return 0


node_sort = cmp_to_key(node_cmp)


def color_state(state: str) -> Text:
    if state == "RUN":
        return Text(state, style='green')
    if state == "INIT":
        return Text(state, style='yellow')
    if state == "ERROR":
        return Text(state, style='bold red')
    else:
        return Text(state)
