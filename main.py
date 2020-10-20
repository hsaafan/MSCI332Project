import gurobipy as gp
from gurobipy import GRB

import data_import


def main():
    try:
        # Create model
        m = gp.Model("mip1")

        # Add variables
        products = data_import.import_products()
        machines = data_import.import_machines()

        var_dict = {}
        for item in products:
            item_id = f"{int(item['id']):02}"
            # Decision variable
            var_dict['x' + item_id] = m.addVar(vtype=GRB.INTEGER)
            var_dict['x' + item_id].varName = 'x' + item_id
            # Surplus variable for demand
            var_dict['y+' + item_id] = m.addVar(vtype=GRB.CONTINUOUS)
            var_dict['y+' + item_id].varName = 'y+' + item_id
            # Slack variable for demand
            var_dict['y-' + item_id] = m.addVar(vtype=GRB.CONTINUOUS)
            var_dict['y-' + item_id].varName = 'y-' + item_id
        for item in machines:
            item_id = f"{int(item['id']):02}"
            var_dict['k' + item_id] = m.addVar(vtype=GRB.BINARY)
            var_dict['k' + item_id].varName = 'k' + item_id

        # Some function definitions to help out with objective and constraints
        def get_demand(i):
            return(var_dict['x'+i] - (var_dict['y+'+i] - var_dict['y-'+i]))

        def get_volumes():
            vol = 0
            for item in products:
                i = f"{int(item['id']):02}"
                vol += var_dict['x'+i] * item['volume']
            return(vol)

        def get_max_volume():
            vol = 0
            for item in machines:
                i = f"{int(item['id']):02}"
                vol += var_dict['k'+i] * item['volume']
            return(vol)

        def get_machines():
            total = 0
            for item in machines:
                i = f"{int(item['id']):02}"
                total += var_dict['k'+i]
            return(total)

        def get_machine_cost():
            cost = 0
            for item in machines:
                i = f"{int(item['id']):02}"
                cost += var_dict['k'+i] * item['cost']
            return(cost)

        def get_demand_slack_penalty():
            penalty = 0
            for item in products:
                i = f"{int(item['id']):02}"
                penalty += var_dict['y-'+i] * item['profit']
            return(penalty)

        # Objective
        mask_short_penalty = 50
        m.setObjective(get_demand_slack_penalty()
                       + get_machine_cost()
                       + mask_short_penalty * var_dict['y-06'],
                       GRB.MINIMIZE)

        # Constraints
        # Demand
        for item in products:
            item_id = f"{int(item['id']):02}"
            m.addConstr(get_demand(item_id) == float(item['demand']),
                        "demand"+item_id)
        # Volume
        m.addConstr(get_volumes() - get_max_volume() <= 0, 'volume')
        # One Machine
        m.addConstr(get_machines() == 1, 'single kiosk')
        # Optimize
        m.optimize()

        # Print results
        print("--------Run Results--------")
        for v in m.getVars():
            print(f'{v.varName:10} {v.x}')
        print(f'Obj: {m.objVal}')

    except gp.GurobiError as e:
        print(f"Error Code: {e.errno} : {e}")
    except AttributeError:
        print("Encountered an attribute error")
    return


if __name__ == "__main__":
    main()
