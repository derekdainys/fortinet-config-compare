from jsondiff import diff
import re
import yaml

def change_indent(config, indent):
    change_indent_config = ""
    for line in config.split("\n"):
        indent_calc = int((len(line) - len(line.lstrip()) )/4)
        
        indentation = " " * indent * indent_calc
        line = line.lstrip()

        change_indent_config += f"{indentation}{line}\n"

    return change_indent_config

def config_compare(running, candidate, config_type="file", indent=4):

    if config_type == "file":
        running_json = config_to_json(config=open(running, "r").read())
        candidate_json = config_to_json(config=open(candidate,"r").read())
    elif config_type == "text":
        running_json = config_to_json(config=running)
        candidate_json = config_to_json(config=candidate)

    compare_json = json_compare(running=running_json, candidate=candidate_json)
    clean_json = json_cleanup(json=compare_json, running=running_json)
    diff = json_to_text(json=clean_json)

    changed_indent = change_indent(config=diff, indent=indent)
    return changed_indent
    
def config_to_json(config):
    regex = re.compile("^(config |set |edit |end$|next$)(.*)")
    indent = 0
    config_lines = config.split("\n")
    json_config = ""

    for line in config_lines:
        if "uuid" in line:
            continue
        if "snmp-index" in line:
            continue
        line = line.strip()
        result = regex.match(line)

        indentation = indent * " "

        if result is not None:
            action = result.group(1).strip()
            data = result.group(2).strip()

            if action == "config":
                data = data.replace(" ", "_")
                data = data.replace('"',"")
                json_config += f"{indentation}{action}_{data}: \n"
                indent += 2

            if action == "set":
                data = data.replace('"','')
                split_data = data.split(" ")

                key = split_data[0]
                split_value = split_data[1:]
                value = " ".join(split_value)

                if "set-community" in key:
                    value = f'"{value}"'
                json_config += f'{indentation}{action}_{key}: {value}\n'

            if action == "edit":
                data = data.replace('"', "")
                json_config += f'{indentation}{action}_"{data}":\n'
                indent += 2

            if action == "next":
                indent += -2

            if action == "end":
                indent += -2

    return yaml.safe_load(json_config)

def dictionary_search(dictionary, find_key):
    if find_key in dictionary:
        return dictionary[find_key]
    for key,value in dictionary.items():
        if isinstance(value, dict):
            result = dictionary_search(value, find_key)
            if result is not None:
                return result
            

def json_cleanup(json, running):
    split_json = json.split("\n")
    json_config = ""
    for line in split_json:

        skips = ["?", "*", "_label"]
        if line.lstrip().startswith(tuple(skips)):
            continue
        
        indent_check = len(line) - len(line.lstrip(" :"))
        line = line.lstrip(" :")

        indentation = indent_check * " "
            
        if "- edit" in line:
            line = line.replace("- edit", "delete")
            json_config += f"{indentation}{line}\n"
        elif "- set" in line:
            line = line.replace("- set", "unset")
            json_config += f"{indentation}{line}\n"
        elif "- config" in line:
            line = line.replace("- config", "config")
            remove_config_lines = remove_config_block(dictionary_search(running, line), indentation_size=indent_check)
            json_config += f"{indentation}{line}\n"
            for remove_config_line in remove_config_lines:
                json_config += remove_config_line
        else:
            json_config += f"{indentation}{line}\n"
        
    return json_config

def json_compare(running, candidate):
    result = diff(running, candidate, syntax="explicit")
    return yaml.dump(result)

def json_to_text(json):
    json_lines = json.split("\n")
    text_config =  ""
    closing_actions = []
    for line_index, line in enumerate(json_lines):
        indentation_calc = (len(line) - len(line.lstrip()))
        full_indentation = indentation_calc
        indentation = full_indentation * " "
        line = line.strip()

        action = line.split("_")[0]
        action = action.replace(":", "")
        action = action.lstrip()

        line = line.replace("_", " ")

        if line_index == len(json_lines) - 1:
            next_line = None
            next_line_indent = 0
        else:
            next_line = json_lines[line_index + 1]
            next_line_indent = (len(next_line) - len(next_line.lstrip()))
            next_line = next_line.strip()

        if action == "config" or action == "edit":
            line = line.replace(":", "")

        if action == "set":
            line = line.replace(":", "", 1)
            text_config += f"{indentation}{line}\n"
            
        elif action == "config":
            text_config += f"{indentation}{line}\n"
            closing_actions.append({"end" : full_indentation})

        elif action == "edit":
            text_config += f"{indentation}{line}\n"
            closing_actions.append({"next" : full_indentation})

        elif action == "delete":
            text_config += f"{indentation}{line}\n"

        elif action == "unset":
            text_config += f"{indentation}{line}\n"

        if next_line_indent < full_indentation:
            for closing_action in closing_actions[::-1]:
                for closer, closing_action_indent in closing_action.items():
                    if closing_action_indent >= next_line_indent:
                        text_config += f"{closing_action_indent * " "}{closer}\n"
                        closing_actions.pop(-1)

    return text_config

def remove_config_block(block, indentation_size=0):
    remove_block_json = ""
    for line in yaml.dump(block).split("\n"):
        indentation_calc = len(line) - len(line.strip())

        indentation = (indentation_calc + indentation_size + 4) * " "      
        if indentation_calc == 0:
            action = line.split("_")[0]
            line = line.replace(":", "")
            line = line.lstrip()

            if action == "edit" or action == "set":
                line = line.replace(":", "")
                line = line.lstrip()

            if action == "edit":
                line = line.replace("edit", "delete")           
                remove_block_json += f"{indentation}{line}\n"
            elif action == "set":
                data = line.split("_")[1]
                data_key = data.split(" ")[0]
                remove_block_json += f"{indentation}unset_{data_key}\n"
            elif action == "config":
                remove_block_json += f"{indentation}{line}\n"
                config_lines = remove_config_block(block=block[line], indentation_size=indentation_size + 2)
                for config_line in config_lines:
                    remove_block_json += config_line

    return remove_block_json

