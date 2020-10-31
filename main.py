import gurobipy as gp
from gurobipy import GRB

import data_import

alpha = 10


def main():
    try:
        # Create model
        m = gp.Model("mip1")
        m.setParam("NonConvex", 2)

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
            # Add bounds to breakpoints
            item['breakpoints'].insert(0, 0)
            item['breakpoints'].append(1e6)
            K = len(item['breakpoints'])
            if K != len(item['marginal_costs']) + 1:
                raise KeyError(f"Length of breakppoints and marginal costs "
                               f"do not match for {item['name']}")
            # SOS2 variable
            sos_vars = []
            for val in range(K):
                s_id = 'z' + item['id'] + f"{val:02}"
                var_dict[s_id] = m.addVar(vtype=GRB.CONTINUOUS)
                var_dict[s_id].varName = s_id
                sos_vars.append(var_dict[s_id])
            m.addSOS(GRB.SOS_TYPE2, sos_vars)
        for item in machines:
            var_dict['k' + item['id']] = m.addVar(vtype=GRB.BINARY)
            var_dict['k' + item['id']].varName = 'k' + item['id']

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

        def get_generic_penalties():
            penalty = 0
            for item in products:
                penalty += var_dict['y-' + item['id']] * item['penalty']
            return(penalty)

        def get_profit(item):
            breakpoints = item['breakpoints']
            costs = item['marginal_costs']
            profit = 0

            def recursive_profit(x, ind):
                if x <= breakpoints[ind + 1]:
                    return(costs[ind] * (x - breakpoints[ind]))
                else:
                    p = recursive_profit(x, ind + 1)

                if ind > 0:
                    p += (costs[ind] * (breakpoints[ind+1] - breakpoints[ind]))
                else:
                    p += costs[ind] * breakpoints[ind + 1]
                return(p)

            for ind in range(len(breakpoints)):
                s_id = 'z' + item['id'] + f"{ind:02}"
                pf = recursive_profit(breakpoints[ind], 0)
                profit += var_dict[s_id] * pf

            return(profit)

        """ Objectives """
        # Machine capital cost
        machine_cost = get_machine_cost() / alpha
        # Short supply penalties
        generic_penalties = get_generic_penalties()
        # Profit loss due to short supply penalty
        # TODO: Update model in report
        # Removed original profit loss because model would set all item
        # stocks to 0 to get a potential profit of 0 which means that no
        # profit is lost by not stocking an item
        profit = 0
        for item in products:
            profit += get_profit(item)

        m.setObjective(machine_cost + generic_penalties - profit)
        """ Constraints """
        # Demand
        for item in products:
            m.addConstr(var_dict['x'+item['id']] - item['demand'] -
                        (var_dict['y+'+item['id']]-var_dict['y-'+item['id']])
                        == 0)
        # Volume
        m.addConstr(get_volumes() - get_max_volume() <= 0, 'volume')
        # One Machine
        m.addConstr(get_machines() == 1, 'single kiosk')
        # SOS2 Equations
        for item in products:
            sum_sos2 = 0
            var_eqn = 0
            for val in range(len(item['breakpoints'])):
                s_id = 'z' + item['id'] + f"{val:02}"
                sum_sos2 += var_dict[s_id]
                var_eqn += var_dict[s_id] * item['breakpoints'][val]
            # Convexity equation
            m.addConstr(sum_sos2 == 1, f"Convexity - {item['name']}")
            # Variable equation
            m.addConstr(var_eqn - var_dict['x' + item['id']] == 0,
                        f"Variable Eqution - {item['name']}")
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
