from enum import Enum
from typing import List, NewType, Callable, Dict
import argparse
import sys
import os
import pathlib
import yaml


# default_arguments: dict = {
#     "verbosity": 0,
#     "ip": "127.0.0.1",
#     "type": "mixed"
# }


class GlobalFlag:
    def __init__(self, name: str, flag: dict):
        self.name = name
        self.short = flag.get("short", "")
        self.long = flag.get("long", "--{}".format(name))
        self.default = flag.get("default")
        self.type = parse_type(flag.get("type"))
        self.help = flag.get("help", "")
        self.metavar = flag.get("metavar")
        self.action = parse_action(flag.get("type"))
        self.choices = flag.get("choices")

        # final_global_flags = List[Callable[str,
        #                                    argparse.ArgumentParser]]
        # for flag in global_flags.items():
        #     flag_short = flag.get("short", "")
        #     flag_long = "--{}".format(flag[0])
        #     flag_default = flag.get("default")
        #     flag_type = self._parse_type(flag.get("type"))
        #     flag_help = flag.get("help", "")

        #     this_func = def

        #     ip_parser = argparse.ArgumentParser(add_help=False)
        #     ip_parser.add_argument(
        #         "-i",
        #         "--ip",
        #         default=default_arguments['ip'],
        #         help="The IP address of the Kraken instance",
        #         dest="{}_ip".format(dest),
        #         metavar="IP_ADDRESS")

        # return global_flags

    def get_parser(self, dest: str) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(add_help=False)
        if self.action == "store_true":
            parser.add_argument(self.short,
                                self.long,
                                action=self.action,
                                help=self.help,
                                dest="{}_{}".format(dest, self.name))
        else:
            parser.add_argument(self.short,
                                self.long,
                                choices=self.choices,
                                action=self.action,
                                default=self.default,
                                help=self.help,
                                dest="{}_{}".format(dest, self.name),
                                metavar=self.metavar)

        return parser


class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


class ArgumentManager:
    def __init__(self, function_map: Dict[str, Callable[[dict], None]], cli_layout_filename: str):
        yaml_dict = {}
        self.global_flags: List[GlobalFlag] = []
        yaml_actions = {}
        entry_point = ""
        entry_help = ""

        file_location = "{}/{}".format(os.path.dirname(
            os.path.realpath(__file__)), cli_layout_filename)
        # print(file_location)
        with open(file_location, 'r') as stream:
            try:
                yaml_dict = yaml.safe_load(stream)
                # print(yaml_dict)
            except yaml.YAMLError as exc:
                print(exc)

        if len(yaml_dict.keys()) == 1:
            entry_point = list(yaml_dict.keys())[0]
            global_flags = yaml_dict[entry_point].get("global_optional_flags")
            actions = yaml_dict[entry_point].get("actions")
            entry_help = yaml_dict[entry_point].get("help")

            if global_flags is not None:
                self.global_flags = self._parse_global_flags(global_flags)

            if actions is not None:
                yaml_actions = actions
            else:
                print("could not find any actions in {}".format(
                    cli_layout_filename))
                sys.exit(1)
        else:
            print("found more than one entry point in {}".format(
                cli_layout_filename))
            sys.exit(1)

        self.function_map = function_map

        self.parser = MyParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                               parents=self._get_global_parents(entry_point))

        # Same subparsers as usual
        self.main_commands = self.parser.add_subparsers(
            help=entry_help, dest=entry_point, metavar="action", required=True)

        self._parse_actions(self.main_commands, yaml_actions)

    # def add_layout(self, cli_layout: dict):
    #     pass

    def _get_global_parents(self, dest: str) -> List[argparse.ArgumentParser]:
        parser_list: List[argparse.ArgumentParser] = []
        for flag in self.global_flags:
            parser_list.append(flag.get_parser(dest))

        return parser_list

    def _parse_global_flags(self, global_flags: dict) -> List[GlobalFlag]:
        final_global_flags: List[GlobalFlag] = []
        for flag in global_flags.items():
            global_flag = GlobalFlag(flag[0], flag[1])
            final_global_flags.append(global_flag)
            # flag_short = flag.get("short", "")
            # flag_long = "--{}".format(flag[0])
            # flag_default = flag.get("default")
            # flag_type = self._parse_type(flag.get("type"))
            # flag_help = flag.get("help", "")

            # this_func = def

            # ip_parser = argparse.ArgumentParser(add_help=False)
            # ip_parser.add_argument(
            #     "-i",
            #     "--ip",
            #     default=default_arguments['ip'],
            #     help="The IP address of the Kraken instance",
            #     dest="{}_ip".format(dest),
            #     metavar="IP_ADDRESS")

        return final_global_flags

    def _parse_actions(self, subparser: argparse._SubParsersAction, actions: dict) -> argparse._SubParsersAction:
        for action in actions.items():
            parser_dest = "{}_{}".format(subparser.dest, action[0])
            parser_help = action[1].get("help", "")
            this_parser = subparser.add_parser(
                action[0],
                help=parser_help,
                parents=self._get_global_parents(parser_dest))
            if "actions" in action[1]:
                # this needs to be another subparser
                subparsers = this_parser.add_subparsers(
                    help=parser_help, dest=parser_dest, metavar="{}_action".format(action[0]), required=True)
                self._parse_actions(subparsers, action[1]["actions"])
            elif "func" in action[1]:
                # this needs to be a regular parser
                parser_func = self.function_map.get(action[1]["func"], None)
                this_parser.set_defaults(func=parser_func)
                if "optional_flags" in action[1]:
                    self._parse_optional_flags(
                        this_parser,
                        action[1]["optional_flags"],
                        parser_dest)
                if "arguments" in action[1]:
                    self._parse_arguments(
                        this_parser,
                        action[1]["arguments"],
                        parser_dest)

    def _parse_optional_flags(self, parser: argparse.ArgumentParser, optional_flags: dict, parent_dest: str) -> argparse.ArgumentParser:
        # dsc_cfg_parser = argparse.ArgumentParser(add_help=False)
        for flag in optional_flags.items():
            flag_type = parse_type(flag[1].get("type"))
            flag_default = flag[1].get("default")
            flag_dest = self._create_dest(parent_dest, flag[0])
            flag_action = parse_action(flag[1].get("type"))
            flag_help = flag[1].get("help", "")
            flag_metavar = flag[1].get("metavar")
            flag_choices = flag[1].get("choices")
            flag_string = "--{}".format(flag[0])
            flag_short = flag[1].get("short")
            if flag_short is None:
                parser.add_argument(
                    flag_string,
                    choices=flag_choices,
                    type=flag_type,
                    default=flag_default,
                    dest=flag_dest,
                    action=flag_action,
                    help=flag_help,
                    metavar=flag_metavar,
                    required=False
                )
            else:
                parser.add_argument(
                    flag_short,
                    flag_string,
                    choices=flag_choices,
                    type=flag_type,
                    default=flag_default,
                    dest=flag_dest,
                    action=flag_action,
                    help=flag_help,
                    metavar=flag_metavar,
                    required=False
                )
        # parser.add_argument(
        #     "--type",
        #     choices=["dsc", "cfg", "mixed"],
        #     type=str.lower,
        #     default=default_arguments['type'],
        #     dest="{}_type".format(dest),
        #     action='store_true',
        #     help="The type of node state you want. cfg, dsc, or mixed",
        #     metavar="STATE_TYPE")

    def _parse_arguments(self, parser: argparse.ArgumentParser, arguments: dict, parent_dest: str) -> argparse.ArgumentParser:
        for argument in arguments.items():
            arg_type = parse_type(argument[1].get("type"))
            arg_dest = self._create_dest(parent_dest, argument[0])
            arg_action = parse_action(argument[1].get("type"))
            arg_help = argument[1].get("help", "")
            arg_metavar = argument[1].get("metavar")
            arg_choices = argument[1].get("choices")
            parser.add_argument(
                # arg_dest,
                choices=arg_choices,
                type=arg_type,
                dest=arg_dest,
                action=arg_action,
                help=arg_help,
                metavar=arg_metavar,
            )

    def _create_dest(self, parent: str, child: str) -> str:
        return "{}_{}".format(parent, child)

    # def add_action(self, name: str, options: List[OptionalArgument], help: str, func: Callable[[dict], None]) -> argparse.ArgumentParser:
    #     parents: List[argparse.ArgumentParser] = []
    #     for option in options:
    #         parents.append(option(name))
    #     this_parser = self.main_commands.add_parser(
    #         name, parents=parents, help=help)
    #     this_parser.set_defaults(func=func)

    #     return this_parser

    def parse_args(self):
        args = self.parser.parse_args()

        non_defaults: dict = {}

        default_arguments: dict = {}
        for flag in self.global_flags:
            default_arguments[flag.name] = flag.default

        # go through each cli argument and check if it isn't a default
        for argument in vars(args).items():
            found_default = False
            for default in default_arguments.items():
                if default[0] in argument[0]:
                    found_default = True
                    # check if this argument is actually the default
                    if default[1] != argument[1]:
                        # this argument is not the default
                        non_defaults[default[0]] = argument[1]

            if not found_default:
                non_defaults[argument[0]] = argument[1]

        config_args = get_config(
            default_arguments, non_defaults.get("debug"))

        # go through each config argument (that hasn't already been set from the cli) and check if it isn't a default
        for argument in config_args.items():
            if argument[0] not in non_defaults.keys():
                found_default = False
                for default in default_arguments.items():
                    if default[0] in argument[0]:
                        found_default = True
                        # check if this argument is actually the default
                        if default[1] != argument[1]:
                            # this argument is not the default
                            non_defaults[default[0]] = argument[1]

                if not found_default:
                    non_defaults[argument[0]] = argument[1]

        # fill in any missing arguments with the defaults
        for default in default_arguments.items():
            if default[0] not in non_defaults.keys():
                non_defaults[default[0]] = default[1]

        # print(args)
        # print("non_defaults:{}".format(non_defaults))

        if vars(args)['func'] is not None:
            args.func(non_defaults)
        else:
            print("This command is not yet implemented")

        # find all repeating regex
        # initial_regex = r'(\w+?)_(\w+)'

        # parser = verbosity_parser("blah")
        # print(parser)
        # print(parser.get_default("blah"))

        # # namespace.get_default("main_verbosity")

        # for argument in vars(namespace).keys():
        #     print(argument)

        # new_namespace = argparse.Namespace(blah="yo")
        # print(new_namespace)

        # print(args)


def parse_type(yaml_type: str) -> object:
    if yaml_type == None:
        return None
    if yaml_type == "string":
        return str.lower
    if yaml_type == "enum":
        return str.lower
    if yaml_type == "str":
        return str.lower
    if yaml_type == "int":
        return int
    if yaml_type == "float":
        return float
    if yaml_type == "path":
        return pathlib.Path
    return None


def parse_action(yaml_type: str) -> str:
    if yaml_type == "bool":
        return "store_true"
    return "store"


def get_config(defaults: dict, debug: bool) -> dict:
    # check to see if config exists in home directory
    # home = str(pathlib.Path.home())
    home = pathlib.Path.home()
    config_path = home / ".krakenctl"

    # if it does exist, use it
    try:
        with open(config_path) as file:
            if debug:
                print("found config file at: {}".format(config_path))
            try:
                yaml_dict = yaml.safe_load(file)
                return yaml_dict
                # print(yaml_dict)
            except yaml.YAMLError as exc:
                if debug:
                    print("error while loading config: {}\nusing defaults".format(exc))
                return defaults

    # if it doens't exist, try to create it
    except:
        if debug:
            print("could not find file at: {}\ncreating one with defaults".format(
                config_path))
        with open(config_path, 'w') as file:
            documents = yaml.dump(defaults, file)
            return defaults
