#!/usr/bin/env python3

# from argument_manager import ArgumentManager, OptionalArgument
from argument_manager import ArgumentManager
import yaml
import os
import requests
import sys
from table import print_table


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
    file_location = args.get("krash_node_create_node_config")
    url = build_url(args.get("ip"), "cfg/nodes")
    send_file(url, "POST", file_location)


def node_update(args):
    # print("node update got these args: {}".format(args))
    file_location = args.get("krash_node_update_node_config")
    url = build_url(args.get("ip"), "cfg/nodes")
    send_file(url, "PUT", file_location)


def node_list(args: dict):
    print("node list got args: {}".format(args))

    if args['krash_node_list_type'] == 'cfg':
        print("state type is cfg")
    elif args['krash_node_list_type'] == 'dsc':
        print("state type is dsc")
    elif args['krash_node_list_type'] == 'mixed':
        print("state type is mixed")
    # print("args: {}".format(args))
    url = build_url(args.get("ip"), "cfg/nodes")
    json = get_url(url)
    # print(json)
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


def send_file(url: str, type: str, file_location: str) -> None:
    if os.path.isfile(file_location):
        if type == "POST":
            try:
                r = requests.post(url, data=open(file_location, 'rb'))
                if r.ok:
                    json = r.json()
                    print("json response: {}".format(json))
                else:
                    print(
                        "ERROR: response returned non-ok status code: {}".format(r.status_code))
            except requests.exceptions.RequestException as e:
                print("ERROR: exception occured while POSTing data: {}".format(e))
        elif type == "PUT":
            try:
                r = requests.put(url, data=open(file_location, 'rb'))
                if r.ok:
                    json = r.json()
                    print("json response: {}".format(json))
                else:
                    print(
                        "ERROR: response returned non-ok status code: {}".format(r.status_code))
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


if __name__ == "__main__":
    main()
