import numpy as np

import data_import


def construction_heurestic_function(alpha: float, n: int, m: int,
                                    V_machines: np.ndarray, c: np.ndarray,
                                    v_products: np.ndarray, f: list, p: list,
                                    mu: np.ndarray, sigma: np.ndarray,
                                    m_penalty: np.ndarray):
    k = np.zeros_like(V_machines)
    k[0] = 1
    V_current = V_machines[0]
    x = np.zeros((m, 1))
    d = np.zeros((m, 1))
    ym = np.zeros((m, 1))
    for i in range(m):
        v_i = v_products[i]
        x_capacity = np.floor(min(V_current/v_i, mu[i]))
        for j in range(i):
            if sigma[i, j] < 0:
                x_capacity = 0
        x[i] = x_capacity
        V_current -= x[i] * v_i
    for i in range(m):
        sigma_i = sigma[i].reshape((-1, 1))
        d[i] = mu[i] + x[i] * (x.T @ sigma_i)
        ym[i] = d[i] - x[i]
    z_x = calculate_SOS2_variables(f, x)
    z_d = calculate_SOS2_variables(f, d)
    Z = calculate_objective_function(m, p, z_x, z_d, alpha,
                                     c, k, ym, m_penalty)
    return(Z, k, x)


def calculate_SOS2_variables(f: list, x: np.ndarray):
    z = []
    for i, x_i in enumerate(x):
        z_i = np.zeros_like(f[i])
        for k, f_k in enumerate(f[i]):
            if k == 0:
                pass
            elif f_prev <= x_i <= f_k:
                z_i[k - 1] = (x_i - f_prev) / (f_k - f_prev)
                z_i[k] = 1 - z_i[k - 1]
            f_prev = f_k
        z.append(z_i)
    return(z)


def calculate_objective_function(m: int, p: list, z_x: list, z_d: list,
                                 alpha: float, c: np.ndarray, k: np.ndarray,
                                 ym: np.ndarray, m_penalty: np.ndarray):
    profit_potential = 0
    profit_met = 0
    for i in range(m):
        z_d_i = z_d[i].reshape((-1, 1))
        z_x_i = z_x[i].reshape((-1, 1))
        p_i = p[i].reshape((-1, 1))
        profit_potential += z_d_i.T @ p_i
        profit_met += z_x_i.T @ p_i
    machine_cost = (c.reshape((-1, 1)).T @ k.reshape((-1, 1))) / alpha
    short_penalty = m_penalty.reshape((-1, 1)).T @ ym.reshape((-1, 1))
    return(profit_potential-profit_met + machine_cost + short_penalty)


if __name__ == "__main__":
    alpha = 10
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

    Z, k, x = construction_heurestic_function(alpha, n, m, V_machines, c,
                                              v_products, f, p, mu, sigma,
                                              m_penalty)
    print(Z, k, x)
