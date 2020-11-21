import matplotlib.pyplot as plt
import numpy as np
import time
import generate_random_data
import data_import
from construction import construction_heurestic_function as chf
import annealing

# Model Parameter
alpha = 10

# Simulated Annealing Parameters
T_sa = 4000
m_sa = 10
k_sa = 10
alpha_sa = 0.2


def test_input_size_construction():
    number_products = np.linspace(50, 1000, num=50, dtype=int)
    times = []
    samples = 25

    for m in number_products:
        sample_times = []
        for i in range(samples):
            parameters = generate_random_data.generate_test_data(m)
            V_machines, c, v_products, f, p, mu, m_p = parameters
            start = time.time()
            chf(alpha, V_machines, c, v_products, f, p, mu, m_p)
            end = time.time()
            sample_times.append(end-start)
        times.append(np.mean(sample_times))

    plt.scatter(number_products, times)
    plt.title("Construction Heurestic")
    plt.xlabel("Number of Products")
    plt.ylabel("Construction Runtime (s)")
    plt.show()
    return


def test_input_size_annealing():
    number_products = np.linspace(50, 500, num=10, dtype=int)
    times = []
    samples = 5

    for m in number_products:
        sample_times = []
        for i in range(samples):
            parameters = generate_random_data.generate_test_data(m)
            V_machines, c, v_products, f, p, mu, m_p = parameters
            Z, k, x = chf(alpha, V_machines, c, v_products, f, p, mu, m_p)
            start = time.time()
            annealing.simulatedAnnealing(x, k, m_sa, k_sa, alpha_sa, T_sa, alpha, v_products, mu, p, V_machines, c, m_p, f)
            end = time.time()
            sample_times.append(end-start)
        times.append(np.mean(sample_times))

    plt.scatter(number_products, times)
    plt.title("Simulated Annealing")
    plt.xlabel("Number of Products")
    plt.ylabel("Runtime (s)")
    plt.show()
    return


def test_objective_value():
    V_machines, c, v_products, f, p, mu, m_p = data_import.import_as_arrays()
    Z, k, x = chf(alpha, V_machines, c, v_products, f, p, mu, m_p)
    Zc, Zinc = annealing.simulatedAnnealing(x, k, m_sa, k_sa, alpha_sa, T_sa, alpha, v_products, mu, p, V_machines, c, m_p, f)
    Zc = np.asarray(Zc).flat
    Zinc = np.asarray(Zinc).flat
    plt.plot(Zc, label='Current Objective Value')
    plt.plot(Zinc, label='Incumbent Objective Value')
    plt.legend()
    plt.title("Simulated Annealing")
    plt.xlabel("Step")
    plt.ylabel("Objective Function Value")
    plt.show()
    return


if __name__ == "__main__":
    test_objective_value()
