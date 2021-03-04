#!/usr/bin/env python3

# from argument_manager import ArgumentManager, OptionalArgument
from argument_manager import ArgumentManager
import yaml
import os
import requests
import sys
from table import print_table
import pprint


def main():
    function_map = {
        "node_list": node_list,
        "node_create": node_create,
        "node_update": node_update
    }

    argument_manager = ArgumentManager(function_map, "cli-layout.yaml")
    argument_manager.parse_args()


def node_create(args):
    # print("node create got these args: {}".format(args))
    verbose = args.get("verbose")
    debug = args.get("debug")
    file_location = args.get("krakenctl_node_create_node_config")

    url = build_url(args.get("ip"), "cfg/nodes")
    send_file(url, "POST", file_location, debug, verbose)


def node_update(args):
    # print("node update got these args: {}".format(args))
    verbose = args.get("verbose")
    debug = args.get("debug")
    file_location = args.get("krakenctl_node_update_node_config")

    url = build_url(args.get("ip"), "cfg/nodes")
    send_file(url, "PUT", file_location, debug, verbose)


def node_list(args: dict):
    verbose = args.get('verbose')
    ip = args.get("ip")
    debug = args.get('debug')
    if debug:
        print("node list got args: {}".format(args))

    dsc_url = build_url(ip, "dsc/nodes")
    cfg_url = build_url(ip, "cfg/nodes")

    if args['krakenctl_node_list_type'] == 'cfg':
        if debug:
            print("state type is cfg")
        json = get_url(cfg_url)
    elif args['krakenctl_node_list_type'] == 'dsc':
        if debug:
            print("state type is dsc")
        json = get_url(dsc_url)
    elif args['krakenctl_node_list_type'] == 'mixed':
        if debug:
            print("state type is mixed")
        cfg_json = get_url(cfg_url)
        dsc_json = get_url(dsc_url)
        json = merge_dict(cfg_json, dsc_json)

    print_table(json['nodes'], verbose=args.get("verbose"))


def get_url(url: str) -> dict:
    # hardcoded_ip = "192.168.57.10:3141"
    try:
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


def send_file(url: str, type: str, file_location: str, debug=False, verbose=False) -> None:
    if os.path.isfile(file_location):
        if type == "POST":
            try:
                r = requests.post(url, data=open(file_location, 'rb'))
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
                r = requests.put(url, data=open(file_location, 'rb'))
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
    else:
        print("ERROR: path does not exist: {}".format(file_location))
        sys.exit(1)


def build_url(ip: str, url: str) -> str:
    return "http://{}/{}".format(ip, url)


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
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dict(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            elif isinstance(a[key], list) and isinstance(b[key], list):
                a[key] = merge_list(a[key], b[key])
            else:
                a[key] = b[key]
                # raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


if __name__ == "__main__":
    main()
