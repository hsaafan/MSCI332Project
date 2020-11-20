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


def import_as_arrays(product_path='products', machine_path='machines'):
    # Import products and machines
    products, sigma = import_products(product_path)
    machines = import_machines(machine_path)

    n = len(machines)
    m = len(products)
    V_machines = np.zeros((n, 1))
    c = np.zeros((n, 1))
    v_products = np.zeros((m, 1))
    mu = np.zeros((m, 1))
    m_penalty = np.zeros((m, 1))
    f = []
    p = []

    # Place parameter values into arrays
    for i, item in enumerate(machines):
        V_machines[i] = item['volume']
        c[i] = item['cost']

    for i, item in enumerate(products):
        v_products[i] = item['volume']
        mu[i] = item['demand']
        m_penalty[i] = item['penalty']
        f_i = item['breakpoints']
        f_i.insert(0, 0)
        f_i.append(1e3)
        f.append(np.asarray(f_i))
        p_i = [0]
        for j, cost in enumerate(item['marginal_costs']):
            p_i.append(p_i[-1] + cost * (f_i[j + 1] - f_i[j]))
        p.append(np.asarray(p_i))
    return(V_machines, c, v_products, f, p, mu, m_penalty)


if __name__ == "__main__":
    print("File is a module, not a script")
