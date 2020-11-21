import sys
import random
import copy
import math
import numpy as np
from construction import *


def simulatedAnnealing(xi, kn, m, k, alpha, T, beta, volume, demand, p,
                       kioskVolume, kioskCost, penalty, f):
    # Checks that a solution meets all constraints, else throws errors
    ym = calc_ym(xi, demand)

    print("Initial Solution")
    z_x = calculate_SOS2_variables(f, xi)
    z_d = calculate_SOS2_variables(f, demand)
    Z = calculate_objective_function(p, z_x, z_d, beta,
                                     kioskCost, kn, ym, penalty)
    print("xi: ", xi, "kn: ", kn, "z = ", Z)

    # Initialize incumbent values with initial solution
    incXi = copy.deepcopy(xi)
    incKn = copy.deepcopy(kn)

    # Iterate through solution

    Zc_array = []
    Zinc_array = []
    for i in range(m*k):
        xi, kn, incXi, incKn, Zc, Zinc = newSolution(xi, kn, T, beta, volume,
                                                     demand, p, kioskVolume,
                                                     kioskCost, incXi, incKn,
                                                     penalty, f)
        Zc_array.append(Zc)
        Zinc_array.append(Zinc)
        if i % m == 0:
            T = alpha * T

    # Print final solution
    incYm = calc_ym(incXi, demand)
    print("Final Solution")
    z_x = calculate_SOS2_variables(f, incXi)
    z_d = calculate_SOS2_variables(f, demand)
    Z = calculate_objective_function(p, z_x, z_d, beta, kioskCost,
                                     incKn, incYm, penalty)
    print("xi: ", incXi, "kn: ", incKn, "z = ", Z)
    return(Zc_array, Zinc_array)


def newSolution(xi, kn, T, beta, volume, demand, p, kioskVolume,
                kioskCost, incXi, incKn, penalty, f):
    # Create temporary xi and kn values
    nxi = copy.deepcopy(xi)
    nkn = copy.deepcopy(kn)

    # Randomly pick variable to modify
    leaving = generateLeaving(nxi)

    # Modify kiosk selection
    if leaving == len(nxi):
        # Update kn list
        oldKiosk = leavingKiosk(nkn)
        newKiosk = newK(oldKiosk)
        nkn[oldKiosk] = 0
        nkn[newKiosk] = 1

        # Adjust xi values to fit volume
        currentVolume = kioskVolume[oldKiosk]
        i = 0
        if kioskVolume[oldKiosk] > kioskVolume[newKiosk]:
            while currentVolume > kioskVolume[newKiosk]:
                if nxi[i] > 0 and currentVolume - volume[i] >= kioskVolume[newKiosk]:
                    nxi[i] = nxi[i] - 1
                    currentVolume = currentVolume - volume[i]
                if i < len(nxi) - 1:
                    i = i + 1
                else:
                    i = 0
        if kioskVolume[oldKiosk] < kioskVolume[newKiosk]:
            while currentVolume < kioskVolume[newKiosk]:
                if nxi[i] + 1 <= demand[i] and currentVolume + volume[i] <= kioskVolume[newKiosk]:
                    nxi[i] = nxi[i] + 1
                    currentVolume = currentVolume + volume[i]
                if i < len(nxi) - 1:
                    i = i + 1
                else:
                    i = 0

    # Modify xi values
    else:
        add = generateAdd(leaving, nxi, volume, demand)

        if volume[add]/volume[leaving] == 1:
            nxi[leaving] = nxi[leaving] - 1
            nxi[add] = nxi[add] + 1
        elif volume[add]/volume[leaving] == 2:
            nxi[leaving] = nxi[leaving] - 2
            nxi[add] = nxi[add] + 1
        else:
            nxi[leaving] = nxi[leaving] - 1
            nxi[add] = nxi[add] + 2

    # Ensure that new solution meets constraints
    check_Constraints(nxi, nkn, volume, kioskVolume)

    nym = calc_ym(nxi, demand)
    ym = calc_ym(xi, demand)
    incYm = calc_ym(incXi, demand)

    # Calculate SOS2 variables
    z_nx = calculate_SOS2_variables(f, nxi)
    z_x = calculate_SOS2_variables(f, xi)
    z_incx = calculate_SOS2_variables(f, incXi)
    z_d = calculate_SOS2_variables(f, demand)

    # Calculate objective function
    Zn = calculate_objective_function(p, z_nx, z_d, beta,
                                      kioskCost, nkn, nym, penalty)
    Zc = calculate_objective_function(p, z_x, z_d, beta,
                                      kioskCost, kn, ym, penalty)

    # Keep solution with lower objective value
    if Zn < Zc:
        xi = copy.deepcopy(nxi)
        kn = copy.deepcopy(nkn)

    # Keep solution with higher objective value with some probability
    elif random.uniform(0, 1) <= math.exp((Zc-Zn)/T):
        xi = copy.deepcopy(nxi)
        kn = copy.deepcopy(nkn)

    # If new solution has lower objective value than the
    # incumbent, replace incumbent with new solution
    Zinc = calculate_objective_function(p, z_incx, z_d, beta,
                                        kioskCost, incKn, incYm, penalty)
    if Zn < Zinc:
        incXi = copy.deepcopy(nxi)
        incKn = copy.deepcopy(nkn)

    return xi, kn, incXi, incKn, Zc, Zinc


def calc_ym(xi, demand):
    # Calculate unmet demand
    ym = copy.deepcopy(demand)
    for i in range(len(xi)):
        ym[i] = demand[i] - xi[i] 
    return ym


def check_Constraints(testxi, testkn, volume, kioskVolume):
    # Check that solution meets all constraints
    # Check xi values are positive integers
    # Calculate total product volume and check for exceeding demand
    totalVolume = 0
    for i in range(len(testxi)):
        if not isinstance(testxi[i][0], np.integer):
            print(i)
            raise RuntimeError("Error: xi value is not integer")
        if testxi[i] < 0:
            print(i)
            raise RuntimeError("Error: xi value is negative")
        totalVolume = totalVolume + testxi[i]*volume[i]

    # Check kn values are binary
    # Calculate volume of selected kiosk and count how many kiosks are selected
    kioskCount = 0
    selectedKioskVolume = 0
    for n in range(len(testkn)):
        if testkn[n] != 0 and testkn[n] != 1:
            sys.exit("Error: kn value not binary")
        kioskCount = kioskCount + testkn[n]
        selectedKioskVolume = selectedKioskVolume + testkn[n]*kioskVolume[n]
    # Check number of kiosks selected
    if kioskCount > 1:
        sys.exit("Error: Multiple kiosks selected")
    elif kioskCount < 1:
        sys.exit("Error: No kiosk selected")
    # Check if product volume exceeds kiosk capacity
    if totalVolume > selectedKioskVolume:
        print(selectedKioskVolume, totalVolume, volume)
        sys.exit("Error: Exceeded Kiosk Volume")


def generateLeaving(xi):
    # Randomly picks leaving xi value and verifies feasibility
    leaving = random.randint(0, len(xi))
    if leaving == len(xi):  # Not associated with any xi, change the kn value
        return leaving
    elif xi[leaving] != 0:  # Check if leaving value already 0
        return leaving
    else:
        return generateLeaving(xi)


def generateAdd(leaving, xi, volume, demand):
    # Randomly picks incoming xi value and verifies feasibility
    add = random.randint(0, len(xi)-1)
    if add == leaving:  # Checks if incoming xi matches leaving xi
        return generateAdd(leaving, xi, volume, demand)
    if volume[add]/volume[leaving] > 1 and xi[leaving] < 2:
        # Checks if volume of incoming product requires
        # more slots than leaving xi has
        return generateAdd(leaving, xi, volume, demand)
    else:
        return add


def leavingKiosk(kn):
    # Determines which kiosk is leaving
    for i in range(len(kn)):
        if kn[i] == 1:
            return i


def newK(oldKiosk):
    # Determines which kiosk is replacing leaving kiosk
    R = random.randint(0, 2)
    if R == oldKiosk:
        return newK(oldKiosk)
    else:
        return R
