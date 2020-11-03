import gurobipy as gp
from gurobipy import GRB

import data_import

alpha = 10
# Decision variable definitions for products
DECISION_VARS = {
    'x':                        # Key in code, do not change
    {
        'name': 'x',            # Name in console output
        'sos2': False,          # Is this is a set of SOS2 variables?
        'sos_group': None,      # Which piecewise function is the sos2 set for?
        'vtype': GRB.INTEGER    # Gurobi variable type
    },
    'y_p':
    {
        'name': 'y+',
        'sos2': False,
        'sos_group': None,
        'vtype': GRB.CONTINUOUS
    },
    'y_m':
    {
        'name': 'y-',
        'sos2': False,
        'sos_group': None,
        'vtype': GRB.CONTINUOUS
    },
    'zx':
    {
        'name': 'zx',
        'sos2': True,
        'sos_group': 'product - volume discount',
        'vtype': GRB.CONTINUOUS
    },
    'zd':
    {
        'name': 'zd',
        'sos2': True,
        'sos_group': 'product - volume discount',
        'vtype': GRB.CONTINUOUS
    },
}


def main():
    try:
        # Create model
        m = gp.Model("mip1")
        m.setParam("NonConvex", 2)

        # Import model parameters
        products, interactions_matrix = data_import.import_products()
        machines = data_import.import_machines()
        var_dict = {}

        for item in products:
            # Add bounds to breakpoints
            item['breakpoints'].insert(0, 0)
            item['breakpoints'].append(1e3)
            # Check that the number of breakpoints and marginal costs match
            K = len(item['breakpoints'])
            if K != len(item['marginal_costs']) + 1:
                raise KeyError(f"Length of breakppoints and marginal costs "
                               f"do not match for {item['name']}")
            # Add all product decision variables to dictionary
            for key, dv in DECISION_VARS.items():
                if dv['sos2'] and 'product' in dv['sos_group']:
                    # Add SOS2 variables for products
                    sos_group = []
                    for val in range(K):
                        name = dv['name'] + item['id'] + f"{val:02}"
                        var_dict[name] = m.addVar(vtype=dv['vtype'])
                        var_dict[name].varName = name
                        sos_group.append(var_dict[name])
                    m.addSOS(GRB.SOS_TYPE2, sos_group)
                else:
                    # Add all other variables
                    name = dv['name'] + item['id']
                    var_dict[name] = m.addVar(vtype=dv['vtype'])
                    var_dict[name].varName = name
        # Decision variables for kiosks
        for item in machines:
            name = 'k' + item['id']
            var_dict[name] = m.addVar(vtype=GRB.BINARY)
            var_dict[name].varName = name

        """ Model Helper functions """
        def get_volumes():
            # Get total volume taken up by products
            vol = 0
            for item in products:
                name = DECISION_VARS['x']['name'] + item['id']
                vol += var_dict[name] * item['volume']
            return(vol)

        def get_max_volume():
            # Get the total volume of the kiosks
            vol = 0
            for item in machines:
                name = 'k' + item['id']
                vol += var_dict[name] * item['volume']
            return(vol)

        def get_machines():
            # Get the number of kiosks used
            total = 0
            for item in machines:
                name = 'k' + item['id']
                total += var_dict[name]
            return(total)

        def get_machine_cost():
            # Get the total cost of the machines
            cost = 0
            for item in machines:
                name = name = 'k' + item['id']
                cost += var_dict[name] * item['cost']
            return(cost)

        def get_generic_penalties():
            # Get the generic penalty costs associated with shorting each item
            penalty = 0
            for item in products:
                name = DECISION_VARS['y_m']['name'] + item['id']
                penalty += var_dict[name] * item['penalty']
            return(penalty)

        def get_profit(sos2_var):
            # Get the expected weekly profit
            total_profit = 0
            for item in products:
                breakpoints = item['breakpoints']
                costs = item['marginal_costs']
                profit = 0

                def recursive_profit(x, i):
                    if x <= breakpoints[i + 1]:
                        return(costs[i] * (x - breakpoints[i]))
                    else:
                        p = recursive_profit(x, i + 1)

                    if i > 0:
                        p += (costs[i] * (breakpoints[i + 1] - breakpoints[i]))
                    else:
                        p += costs[i] * breakpoints[i + 1]
                    return(p)

                for i in range(len(breakpoints)):
                    name = sos2_var['name'] + item['id'] + f"{i:02}"
                    pf = recursive_profit(breakpoints[i], 0)
                    profit += var_dict[name] * pf
                total_profit += profit
            return(total_profit)

        def get_demand(item):
            expected = item['demand']
            interactions = 0
            name = DECISION_VARS['x']['name'] + item['id']
            xi = var_dict[name]
            i = int(item['id']) - 1
            for j, item2 in enumerate(products):
                xj = var_dict['x' + item2['id']]
                interactions += xi * xj * interactions_matrix[i, j]
            return(expected + interactions)

        """ Helper functions for statistics """
        def get_demand_evaluation(item):
            expected = item['demand']
            interactions = 0
            name = DECISION_VARS['x']['name'] + item['id']
            xi = var_dict[name].x
            i = int(item['id']) - 1
            for j, item2 in enumerate(products):
                xj = var_dict['x' + item2['id']].x
                interactions += xi * xj * interactions_matrix[i, j]
            return(expected + interactions)

        def get_demand_fraction(essential=False):
            demand = 0
            stocked = 0
            for item in products:
                if essential and item['penalty'] <= 0:
                    # Skip items that have no additional penalty
                    continue
                name = DECISION_VARS['x']['name'] + item['id']
                stocked += var_dict[name].x
                demand += get_demand_evaluation(item)
            return(stocked/demand)

        """ Model Objectives """
        # Machine capital cost
        machine_cost = get_machine_cost() / alpha
        # Short supply penalties
        generic_penalties = get_generic_penalties()
        # Profit loss due to short supply penalty
        profit_sold = get_profit(DECISION_VARS['zx'])
        profit_demand = get_profit(DECISION_VARS['zd'])
        stock_short_penalty = profit_demand - profit_sold
        # Final objective function
        m.setObjective(machine_cost + generic_penalties + stock_short_penalty)
        """ Model Constraints """
        # Demand
        for item in products:
            x = DECISION_VARS['x']['name'] + item['id']
            y_p = DECISION_VARS['y_p']['name'] + item['id']
            y_m = DECISION_VARS['y_m']['name'] + item['id']
            m.addQConstr(var_dict[x] - get_demand(item) + var_dict[y_m] == 0,
                         f"demand - {item['name']}")
        # Volume
        m.addConstr(get_volumes() - get_max_volume() <= 0, 'volume')
        # One Machine
        m.addConstr(get_machines() == 1, 'single kiosk')
        # SOS2 Equations
        for item in products:
            for var in ['zx', 'zd']:
                dv = DECISION_VARS[var]
                sum_sos2 = 0
                var_eqn = 0
                for val in range(len(item['breakpoints'])):
                    name = dv['name'] + item['id'] + f"{val:02}"
                    sum_sos2 += var_dict[name]
                    var_eqn += var_dict[name] * item['breakpoints'][val]
                # Convexity equation
                m.addConstr(sum_sos2 == 1, f"Convexity - {item['name']}")
                # Function equations
                if var == 'zx':
                    xi = DECISION_VARS['x']['name'] + item['id']
                    m.addConstr(var_eqn - var_dict[xi] == 0,
                                f"Variable Eqution Stock - {item['name']}")
                elif var == 'zd':
                    m.addQConstr(var_eqn - get_demand(item) == 0,
                                 f"Variable Eqution Demand - {item['name']}")
        # Optimize
        m.update()
        m.optimize()

        # Print results
        print("-----Variable Indices-----")
        print("Index | Name")
        print("====================================")
        for item in products:
            print(f" {int(item['id']):02}   | {item['name']}")
        print("--------Run Results--------")
        print("VarName | Value")
        print("===============")
        for v in m.getVars():
            print(f'{v.varName:7} | {v.x:2.3f}')
            if 'k' in v.varName:
                if v.x > 0:
                    kiosk_picked = v.varName
        print(f'Obj: {m.objVal}')

    except gp.GurobiError as e:
        print(f"Error Code: {e.errno} : {e}")
    except AttributeError:
        print("Encountered an attribute error")
    return({"demand met": get_demand_fraction(),
            "essential_demand_met": get_demand_fraction(True),
            "kiosk chosen": kiosk_picked[-1]})


if __name__ == "__main__":
    print(main())
