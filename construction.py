import numpy as np

import data_import

TOL = 1e-8


def construction_heurestic_function(alpha: float, V_machines: np.ndarray,
                                    c: np.ndarray, v_products: np.ndarray,
                                    f: list, p: list, mu: np.ndarray,
                                    m_penalty: np.ndarray):
    # Get number of machines and number of products
    n = len(V_machines)
    m = len(v_products)
    # Create vectors for decision variables
    k = np.zeros((n, 1))
    x = np.zeros((m, 1))
    ym = np.copy(mu)
    # Choose first machine in list
    k[0] = 1
    V_current = V_machines[0]
    for i in range(m):
        # Get max number of product that can be stocked
        v_i = v_products[i]
        x[i] = np.floor(min(V_current/v_i, mu[i]))
        # Update slack variable and remaining kiosk volume
        ym[i] = mu[i] - x[i]
        V_current -= x[i] * v_i
        if V_current <= TOL:
            # No more room available
            break
    z_x = calculate_SOS2_variables(f, x)
    z_d = calculate_SOS2_variables(f, mu)
    Z = calculate_objective_function(p, z_x, z_d, alpha,
                                     c, k, ym, m_penalty)
    return(Z, k, x)


def calculate_SOS2_variables(f: list, x: np.ndarray):
    # Get number of variables to convert
    n = len(x)
    # Create empty list
    z = [None]*n
    # Iterate through variables
    for i in range(n):
        # Get number of breakpoints for variable
        kappa = len(f[i])
        z[i] = np.zeros((kappa, 1))
        if x[i] <= TOL:
            # First breakpoint is always 0 as per input requirements
            z[i][0] = 1
        else:
            for k in range(1, kappa):
                if f[i][k-1] <= x[i] <= f[i][k]:
                    # Find which 2 breakpoints x is in between
                    z[i][k] = (x[i] - f[i][k-1]) / (f[i][k] - f[i][k-1])
                    z[i][k-1] = 1 - z[i][k]
    return(z)


def calculate_objective_function(p: list, z_x: list, z_d: list, alpha: float,
                                 c: np.ndarray, k: np.ndarray, ym: np.ndarray,
                                 m_penalty: np.ndarray):
    profit_potential = 0
    profit_met = 0
    # Get number of products
    m = len(m_penalty)
    for i in range(m):
        # Calculate profit from each product
        z_d_i = z_d[i].reshape((-1, 1))
        z_x_i = z_x[i].reshape((-1, 1))
        p_i = p[i].reshape((-1, 1))
        # NOTE: @ is numpy shorthand for matrix multiplication
        profit_potential += z_d_i.T @ p_i
        profit_met += z_x_i.T @ p_i
    # Get cost of machine chosen
    machine_cost = (c.reshape((-1, 1)).T @ k.reshape((-1, 1))) / alpha
    # Get penalties for short stocking products
    short_penalty = m_penalty.reshape((-1, 1)).T @ ym.reshape((-1, 1))
    return(profit_potential-profit_met + machine_cost + short_penalty)


if __name__ == "__main__":
    alpha = 10
    # Import products and machines
    products, sigma = data_import.import_products()
    machines = data_import.import_machines()

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

    # Run construction heurestic and print results
    Z, k, x = construction_heurestic_function(alpha, V_machines, c, v_products,
                                              f, p, mu, m_penalty)
    print(f"Objective Value: {Z}\nMachines:\n{k}\nProducts:\n{x}")
