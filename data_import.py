import yaml
import os

import numpy as np


def import_from_yaml(path: str, item_type: str):
    item_list = []
    id_counter = 1
    for yaml_file in os.scandir(path):
        if (yaml_file.path.endswith('.yaml')) and yaml_file.is_file():
            item_file = yaml.load(open(yaml_file, 'r'), Loader=yaml.SafeLoader)
            for key, item in item_file.items():
                if item["type"].lower() == item_type:
                    item["id"] = f"{id_counter:02}"
                    item_list.append(item)
                    id_counter += 1
        else:
            print(f"Skipping {yaml_file}, not a yaml file")
    return(item_list)


def import_products(path='products'):
    product_list = import_from_yaml(path, 'product')
    n = len(product_list)
    interactions = np.zeros((n, n))
    for i, item in enumerate(product_list):
        for inter in item['interactions']:
            j = [key for key, val in enumerate(product_list)
                 if val.get('name') == inter['name']]
            interactions[i, j] = inter['val']
            interactions[j, i] = inter['val']
    return(product_list, interactions)


def import_machines(path='machines'):
    machine_list = import_from_yaml(path, 'machine')
    return(machine_list)


if __name__ == "__main__":
    print("File is a module, not a script")
