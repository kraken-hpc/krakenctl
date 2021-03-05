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

    no_wrap = True
    if verbose:
        no_wrap = False

    for key in columns:
        table.add_column(key, no_wrap=no_wrap)

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
    final_lines.append(final_content)

    if state is not None:
        state_content = Text.assemble(
            "  ", "state", ": ", (color_state(state)), style="bold")
        final_lines.append(state_content)

    return final_lines


def parse_item_short_list(provided_list: list) -> List[Text]:
    final_lines = []

    provided_list.sort(key=list_sort)

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


def parse_item_long(provided_item) -> Text:
    final_string = None
    if type(provided_item) == list:
        list_lines = parse_item_long_list(provided_item, 0)
        final_string = Text("\n").join(list_lines)
    elif type(provided_item) == dict:
        dict_lines = parse_item_long_dict(provided_item, 0)
        final_string = "\n".join(dict_lines)
    else:
        final_string = Text(str(provided_item))

    return final_string


def parse_item_long_list(provided_list: list, level: int) -> List[Text]:
    final_lines = []
    prepend_hyphen = "- "
    prepend_spaces = "  "
    for n in range(level):
        prepend_hyphen = "  " + prepend_hyphen
        prepend_spaces = "  " + prepend_spaces

    prepend_hyphen = Text(prepend_hyphen, Style(bold=True))

    provided_list.sort(key=list_sort)

    for item in provided_list:
        if type(item) == dict:
            dict_lines = parse_item_long_dict(item, level)
            # fix the dictionary so it has a hyphen on the first line
            for i in range(len(dict_lines)):
                if i == 0:
                    dict_lines[0] = Text.assemble(
                        prepend_hyphen, dict_lines[0])
                else:
                    dict_lines[i] = Text.assemble(
                        prepend_spaces, dict_lines[i])
            final_lines.extend(dict_lines)
        else:
            final_content = Text.assemble(
                prepend_spaces, (str(item), Style(bold=False)), style='bold')
            final_lines.append(final_content)

    return final_lines


def parse_item_long_dict(provided_dict: dict, level: int) -> List[Text]:
    final_lines = []

    prepend_spaces = ""
    for n in range(level):
        prepend_spaces = prepend_spaces + "  "

    for item in provided_dict.items():
        if type(item[1]) == dict:
            final_content = Text.assemble(
                prepend_spaces, item[0], ": ", style="bold")
            final_lines.append(final_content)
            sub_dict_lines = parse_item_long_dict(item[1], level + 1)
            final_lines.extend(sub_dict_lines)
        elif type(item[1]) == list:
            sub_list_lines = parse_item_long_list(item[1], level + 1)
            final_lines.extend(sub_list_lines)
        else:
            # print(type(item[1]))
            value = Text(str(item[1]), Style(bold=False))
            if item[0] == "state":
                value = color_state(value)
            final_content = Text.assemble(
                prepend_spaces, item[0], ": ", value, style="bold")
            final_lines.append(final_content)

    return final_lines


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
    b_parent_id = b.get("parentId")
    if not ((a_parent_id is None or a_parent_id == "") and (b_parent_id is None or b_parent_id == "")):
        if a_parent_id is None or a_parent_id == "":
            return -1
        if b_parent_id is None or b_parent_id == "":
            return 1

    a_nodename = a.get("nodename")
    b_nodename = b.get("nodename")
    if not ((a_nodename is None or a_nodename == "") and (b_nodename is None or b_nodename == "")):
        if (a_nodename is None or a_nodename == "") and (b_nodename is not None and b_nodename != ""):
            return -1
        elif (a_nodename is not None and a_nodename != "") and (b_nodename is None or b_nodename == ""):
            return 1
        elif (a_nodename is None or a_nodename == "") and (b_nodename is None or b_nodename == ""):
            return 0
        elif a_nodename > b_nodename:
            return 1
        elif a_nodename < b_nodename:
            return -1

    a_id = a.get("id")
    b_id = b.get("id")
    if not ((a_id is None or a_id == "") and (b_id is None or b_id == "")):
        if (a_id is None or a_id == "") and (b_id is not None and b_id != ""):
            return -1
        elif (a_id is not None and a_id != "") and (b_id is None or b_id == ""):
            return 1
        elif (a_id is None or a_id == "") and (b_id is None or b_id == ""):
            return 0
        elif a_id > b_id:
            return 1
        elif a_id < b_id:
            return -1

    else:
        return 0


node_sort = cmp_to_key(node_cmp)


def list_cmp(a, b):
    if type(a) == dict and type(b) == dict:
        a_type = a.get("@type")
        b_type = b.get("@type")
        if a_type is not None and b_type is not None:
            if a_type > b_type:
                return 1
            elif a_type < b_type:
                return -1
        a_id = a.get("id")
        b_id = b.get("id")
        if a_id is not None and b_id is not None:
            if a_id > b_id:
                return 1
            elif a_id < b_id:
                return -1
    else:
        return 0


list_sort = cmp_to_key(list_cmp)


def color_state(state: str) -> Text:
    if type(state) == Text:
        state = str(state)
    if state == "RUN":
        return Text(state, style='bold green')
    elif state == "INIT" or state == "PHYS_UNKNOWN":
        return Text(state, style='bold yellow')
    elif state == "ERROR" or state == "PHYS_ERROR":
        return Text(state, style='bold red')
    elif state == "SYNC" or state == "POWER_ON":
        return Text(state, style='bold green')
    elif state == "POWER_OFF":
        return Text(state, style='bold light grey')
    elif state == "POWER_CYCLE":
        return Text(state, style='bold purple')
    elif state == "PHYS_HANG":
        return Text(state, style='bold cyan')
    else:
        return Text(state)
