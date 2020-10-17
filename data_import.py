import csv


def import_from_csv(path):
    item_list = []
    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        headers = reader.__next__()
        for row in reader:
            item = {}
            for i in range(len(headers)):
                item[headers[i]] = row[i]
            item_list.append(item)
    return(item_list)


def import_products(path='products.csv'):
    product_list = import_from_csv(path)
    return(product_list)


def import_machines(path='machines.csv'):
    machine_list = import_from_csv(path)
    return(machine_list)


if __name__ == "__main__":
    print("File is a module, not a script")
