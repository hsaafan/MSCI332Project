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
            # Decision variable
            var_dict['x' + item['id']] = m.addVar(vtype=GRB.INTEGER)
            var_dict['x' + item['id']].varName = 'x' + item['id']
            # Surplus variable for demand
            var_dict['y+' + item['id']] = m.addVar(vtype=GRB.CONTINUOUS)
            var_dict['y+' + item['id']].varName = 'y+' + item['id']
            # Slack variable for demand
            var_dict['y-' + item['id']] = m.addVar(vtype=GRB.CONTINUOUS)
            var_dict['y-' + item['id']].varName = 'y-' + item['id']
        for item in machines:
            var_dict['k' + item['id']] = m.addVar(vtype=GRB.BINARY)
            var_dict['k' + item['id']].varName = 'k' + item['id']

        # Some function definitions to help out with objective and constraints
        def get_demand(i):
            return(var_dict['x'+i] - (var_dict['y+'+i] - var_dict['y-'+i]))

        def get_volumes():
            vol = 0
            for item in products:
                vol += var_dict['x' + item['id']] * item['volume']
            return(vol)

        def get_max_volume():
            vol = 0
            for item in machines:
                vol += var_dict['k' + item['id']] * item['volume']
            return(vol)

        def get_machines():
            total = 0
            for item in machines:
                total += var_dict['k' + item['id']]
            return(total)

        def get_machine_cost():
            cost = 0
            for item in machines:
                cost += var_dict['k' + item['id']] * item['cost']
            return(cost)

        def get_demand_slack_penalty():
            penalty = 0
            for item in products:
                penalty += var_dict['y-' + item['id']] * item['profit']
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
            m.addConstr(get_demand(item['id']) == float(item['demand']),
                        "demand"+item['id'])
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
