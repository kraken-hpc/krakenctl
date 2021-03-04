from rich.console import Console
from rich.table import Column, Table
from rich.text import Text
from rich.style import Style
from typing import List
from functools import cmp_to_key
import yaml

special_keys = ["nodename", "id"]


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

    nodes.sort(key=node_sort)

    for node in nodes:
        row_strings = []
        for key in columns:
            column_string = ""
            if key in node.keys():
                if verbose:
                    if key == "runState" or key == "physState":
                        column_string = color_state(parse_item_long(node[key]))
                    else:
                        column_string = parse_item_long(node[key])
                else:
                    if key == "runState" or key == "physState":
                        column_string = color_state(
                            parse_item_short(node[key]))
                    else:
                        column_string = parse_item_short(node[key])
            row_strings.append(column_string)
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

    final_content = Text.assemble(
        "- ", content_key, ": ", (content, Style(bold=False)), style="bold")

    # final_content = Text("- ", style="bold")
    # final_content.append(content_key, style="bold")
    # final_content.append(": ", style="bold")
    # final_content.append(content, style=Style(bold=False))
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
    if type(state) == Text:
        state = str(state)
        # print(str(state))
        # return state
    if state == "RUN":
        return Text(state, style='green')
    if state == "INIT" or state == "PHYS_UNKNOWN":
        return Text(state, style='yellow')
    if state == "ERROR" or state == "PHYS_ERROR":
        return Text(state, style='bold red')
    if state == "SYNC" or state == "POWER_ON":
        return Text(state, style='bold green')
    if state == "POWER_OFF":
        return Text(state, style='light grey')
    if state == "POWER_CYCLE":
        return Text(state, style='purple')
    if state == "PHYS_HANG":
        return Text(state, style='orange')
    else:
        return Text(state)
