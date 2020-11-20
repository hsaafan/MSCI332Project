import matplotlib.pyplot as plt
import numpy as np
import time
import generate_random_data
import construction

alpha = 10


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
            construction.construction_heurestic_function(alpha, V_machines, c,
                                                         v_products, f, p, mu,
                                                         m_p)
            end = time.time()
            sample_times.append(end-start)
        times.append(np.mean(sample_times))

    plt.scatter(number_products, times)
    plt.title("Construction Heurestic")
    plt.xlabel("Number of Products")
    plt.ylabel("Construction Runtime (s)")
    plt.show()
    return


if __name__ == "__main__":
    test_input_size_construction()
