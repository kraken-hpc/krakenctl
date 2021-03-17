#!/usr/bin/env python3

# from argument_manager import ArgumentManager, OptionalArgument
from argument_manager import ArgumentManager
import yaml
import os
import requests
import sys
import json
import copy
from table import print_table
import pprint


def main():
    function_map = {
        "node_list": node_list,
        "node_create": node_create,
        "node_update": node_update,
        "node_info": node_list,
    }

    argument_manager = ArgumentManager(function_map, "cli-layout.yaml")
    argument_manager.parse_args()


def node_create(args: dict):
    verbose = args.get("verbose")
    debug = args.get("debug")
    file_location = args.get("krakenctl_node_create_node_config")

    if debug:
        print("node create got these args: {}".format(args))
        if file_location.name == "<stdin>":
            print("reading from stdin")
        else:
            print("reading from {}".format(file_location.name))

    data = file_location.read()

    url = build_url(args.get("ip"), "cfg/nodes")
    send_json(url, "POST", data, debug, verbose)


def node_update(args: dict):
    verbose = args.get("verbose")
    debug = args.get("debug")
    file_location = args.get("krakenctl_node_update_node_config")

    if debug:
        print("node update got these args: {}".format(args))
        if file_location.name == "<stdin>":
            print("reading from stdin")
        else:
            print("reading from {}".format(file_location.name))

    data = file_location.read()

    url = build_url(args.get("ip"), "cfg/nodes")
    send_json(url, "PUT", data, debug, verbose)


def node_list(args: dict):
    # get all args from cli
    verbose = args.get('verbose')
    ip = args.get('ip')
    debug = args.get('debug')
    filter_string = args.get('krakenctl_node_list_filter')
    node_id = args.get("krakenctl_node_info_node_id")
    list_type = args.get("krakenctl_node_list_type")
    print_json_bool = args.get("krakenctl_node_list_json")

    if debug:
        print("node list got args: {}".format(args))

    # build the urls
    dsc_url = build_url(ip, "dsc/nodes")
    cfg_url = build_url(ip, "cfg/nodes")

    # if a node_id is defined, only get info for that node
    if node_id != None:
        dsc_url = build_url(ip, "dsc/node")
        dsc_url = "{}/{}".format(dsc_url, node_id)
        cfg_url = build_url(ip, "cfg/node")
        cfg_url = "{}/{}".format(cfg_url, node_id)
        list_type = args.get("krakenctl_node_info_type")
        print_json_bool = args.get("krakenctl_node_info_json")
        filter_string = args.get("krakenctl_node_info_filter")
        verbose = True

    # fetch the cfg and dsc data from kraken
    dsc_json = get_url(dsc_url, debug, verbose)
    cfg_json = get_url(cfg_url, debug, verbose)

    # regardless of if we are getting a single node or multiple, put them in their respective lists
    dsc_nodes = []
    cfg_nodes = []

    if node_id != None:
        dsc_nodes = [dsc_json]
        cfg_nodes = [cfg_json]
    else:
        dsc_nodes = dsc_json.get("nodes")
        cfg_nodes = cfg_json.get("nodes")

    # Handle the different types.
    # For dsc we merge in just node names
    # For mixed we merge everything from dsc into cfg
    if list_type == 'cfg':
        if debug:
            print("state type is cfg")
        final_nodes = cfg_nodes
    elif list_type == 'dsc':
        if debug:
            print("state type is dsc")
        final_nodes = merge_nodename(dsc_nodes, cfg_nodes)
    elif list_type == 'mixed':
        if debug:
            print("state type is mixed")
        final_nodes = merge_list(cfg_nodes, dsc_nodes)

    # Do any provided filteres
    if filter_string is not None:
        final_nodes = filter_list(filter_string, final_nodes)
        dsc_nodes = filter_list(filter_string, dsc_nodes)
        cfg_nodes = filter_list(filter_string, cfg_nodes)

    # Print out json or table
    if print_json_bool:
        if node_id != None:
            dsc_nodes = dsc_nodes[0]
            cfg_nodes = cfg_nodes[0]
            final_nodes = final_nodes[0]
        else:
            dsc_nodes = {"nodes": dsc_nodes}
            cfg_nodes = {"nodes": cfg_nodes}
            final_nodes = {"nodes": final_nodes}

        if list_type == 'mixed':
            print("CFG:\n")
            print_json(cfg_nodes, verbose)
            print("\nDSC:\n")
            print_json(dsc_nodes, verbose)
        else:
            print_json(final_nodes, verbose)
    else:
        print_table(final_nodes, verbose=verbose)


def get_url(url: str, debug: bool = False, verbose: bool = False) -> dict:
    # hardcoded_ip = "192.168.57.10:3141"
    try:
        if debug:
            print("requesting {}".format(url))
        r = requests.get(url, timeout=3)
        json = r.json()
        return json
    except requests.exceptions.Timeout:
        print("ERROR: request timed out")
        sys.exit(1)
        # Maybe set up for a retry, or continue in a retry loop
    except requests.exceptions.TooManyRedirects:
        print("ERROR: too many redirects")
        sys.exit(1)
        # Tell the user their URL was bad and try a different one
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        raise SystemExit(e)


def send_json(url: str, type: str, json: str, debug=False, verbose=False) -> None:
    if type == "POST":
        try:
            r = requests.post(url, json)
            if r.ok:
                json = r.json()
                if debug:
                    print("json response: {}".format(json))
                    print("response: {}".format(r))
                if len(json.keys()) == 0:
                    print(
                        "ERROR: kraken returned ok status but didn't return updated state\nCheck provided json file for errors")
                else:
                    print("Success")
        except requests.exceptions.RequestException as e:
            print("ERROR: exception occured while POSTing data: {}".format(e))
    elif type == "PUT":
        try:
            r = requests.put(url, json)
            if r.ok:
                json = r.json()
                if debug:
                    print("json response: {}".format(json))
                    print("response: {}".format(r))
                if len(json.keys()) == 0:
                    print(
                        "ERROR: kraken returned ok status but didn't return updated state\nCheck provided json file for errors")
                else:
                    print("Success")
            else:
                print(
                    "ERROR: response from kraken returned non-ok status code: {}".format(r.status_code))
        except requests.exceptions.RequestException as e:
            print("ERROR: exception occured while PUTing data: {}".format(e))
    else:
        print("received invalid type: {}".format(type))
        sys.exit(1)


def build_url(ip: str, url: str) -> str:
    return "http://{}/{}".format(ip, url)


def print_json(final_json: dict, verbose: bool):
    print(json.dumps(final_json, indent=4, sort_keys=True))


def merge_list(a, b) -> list:
    final_list = []
    for a_item in a:
        found_match = False
        if isinstance(a_item, dict):
            for b_item in b:
                if isinstance(b_item, dict) and not found_match:
                    a_id = a_item.get("id")
                    b_id = b_item.get("id")
                    if a_id is None and b_id is None:
                        a_type = a_item.get("@type")
                        b_type = b_item.get("@type")
                        if a_type == b_type and a_type is not None and b_type is not None:
                            found_match = True
                            merged_item = merge_dict(a_item, b_item)
                            final_list.append(merged_item)
                    elif a_id == b_id and a_id is not None and b_id is not None:
                        found_match = True
                        merged_item = merge_dict(a_item, b_item)
                        final_list.append(merged_item)
    return final_list


def merge_dict(a, b, path=None) -> dict:
    # "merges b into a"
    final_dict = copy.deepcopy(a)
    if path is None:
        path = []
    for key in b:
        if key in final_dict:
            if isinstance(final_dict[key], dict) and isinstance(final_dict[key], dict):
                merge_dict(final_dict[key], b[key], path + [str(key)])
            elif final_dict[key] == b[key]:
                pass  # same leaf value
            elif isinstance(final_dict[key], list) and isinstance(b[key], list):
                final_dict[key] = merge_list(final_dict[key], b[key])
            else:
                final_dict[key] = b[key]
                # raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def merge_nodename(a: list, b: list) -> list:
    a_nodes = copy.deepcopy(a)
    for node in a_nodes:
        node_a_id = node.get("id")
        if node_a_id is not None:
            b_nodes_filtered = list(filter(
                                    lambda x: x.get("id") == node_a_id, b))
            if len(b_nodes_filtered) == 1:
                node_b_nodename = b_nodes_filtered[0].get("nodename")
                if node_b_nodename is not None:
                    node["nodename"] = node_b_nodename

    return a_nodes


def filter_list(filter_string: str, nodes: list) -> list:
    desired_columns = []
    for column in filter_string.split(','):
        desired_columns.append(column.strip())

    if "id" not in desired_columns:
        desired_columns.append("id")
    if "nodename" not in desired_columns:
        desired_columns.append("nodename")

    # print(desired_columns)
    final_nodes = []
    for node in nodes:
        final_node = {}
        for column in desired_columns:
            column_value = node.get(column)
            if column_value is None:
                column_value = ""
            final_node[column] = column_value
            # print(column, column_value)
        final_nodes.append(final_node)

    return final_nodes


if __name__ == "__main__":
    main()
