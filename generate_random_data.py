import data_import
import numpy as np


def get_distributions():
    _, _, v_products, f, p, mu, m = data_import.import_as_arrays()

    # Gaussian distribution for demand
    m_stdv = np.std(m)
    m_mean = np.mean(m)

    # Gaussian distribution for demand
    mu_stdv = np.std(mu)
    mu_mean = np.mean(mu)

    # Probability of volume being 1 or 2
    single_slot_products = np.count_nonzero(np.isclose(v_products, 1))
    p_single_slot = single_slot_products / len(v_products)
    p_double_slot = 1 - p_single_slot

    # Gaussian distribution for prices
    prices = []
    for i in range(len(p)):
        prices.append(p[i][1:] / f[i][1:])
    p_stdv = np.std(prices)
    p_mean = np.mean(prices)

    dist_parameters = {
        'm': [m_mean, m_stdv],
        'mu': [mu_mean, mu_stdv],
        'v': [p_single_slot, p_double_slot],
        'p': [p_mean, p_stdv]
    }
    return(dist_parameters)


def generate_product(dist_parameters):
    m_dist = dist_parameters['m']
    mu_dist = dist_parameters['mu']
    p_dist = dist_parameters['p']

    m = 0
    mu = 0
    p = 0
    while m <= 0:
        m = np.random.normal(m_dist[0], m_dist[1])
    while mu <= 0:
        mu = np.random.normal(mu_dist[0], mu_dist[1])
    while p <= 0:
        p = np.random.normal(p_dist[0], p_dist[1])
    v = np.random.choice([1, 2], p=dist_parameters['v'])
    return(m, mu, p, v)


def generate_multiple_products(num_products=100):
    dists = get_distributions()
    v_products = np.zeros((num_products, 1))
    mu = np.zeros((num_products, 1))
    m_penalty = np.zeros((num_products, 1))
    f = []
    p = []
    for i in range(num_products):
        m_i, mu_i, p_i, v_i = generate_product(dists)
        v_products[i] = v_i
        mu[i] = mu_i
        m_penalty[i] = m_i
        f_i = [0, 1e3]
        f.append(np.asarray(f_i))
        p_i = [0, p_i]
        p.append(np.asarray(p_i))
    return(v_products, f, p, mu, m_penalty)


def generate_test_data(num_products=100):
    v_products, f, p, mu, m_penalty = generate_multiple_products(num_products)
    V_machines, c, _, _, _, _, _ = data_import.import_as_arrays()
    return(V_machines, c, v_products, f, p, mu, m_penalty)
