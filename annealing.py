import sys
import random
import copy
import math
import numpy as np

#Decision Variables
# xi = [4,6,5,3,1,20,1,1,1,6,0,0,0,0]
# kn = [0,1,0]

#Parameters
# m = 10
# k = 10
# alpha = 0.2
# T = 40

# beta = 10 #payback period
# 
# volume = [1,1,1,1,1,1,1,1,1,1,1,1,1,2] #volume must be 1 or 2 spaces
# demand = [4,6,5,3,1,20,1,1,1,10,1,5,5,20]
# profit = [8.75,8.75,8.75,40,20,2,10,10,30,5,10,7,15,8]
# penalty = []
# 
# kioskVolume = [24,48,60]
# kioskCost = [4399,5999,10999]

#Checks that a solution meets all constraints and throws errors if it doesn't
def simulatedAnnealing(xi, kn, m, k, alpha, T, beta, volume, demand, p, kioskVolume, kioskCost, penalty, f):
    ym = calc_ym(xi, demand)
    
    print("Initial Solution")
    print("xi: ", xi, "kn: ", kn, "z = ", calculate_objective_function(p, xi, demand, beta, kioskCost, kn, ym, penalty))
    
    #initialize incumbent values with initial solution
    incXi = copy.deepcopy(xi)
    incKn = copy.deepcopy(kn) 
    
    #iterate through solution
    for i in range(m*k):
        xi, kn, incXi, incKn = newSolution(xi, kn, T, beta, volume, demand, p, kioskVolume, kioskCost, incXi, incKn, penalty, f)
        if i%m == 0:
            T = alpha * T  

    
    #print final solution
    incYm = calc_ym(incXi, demand)   
    print("Final Solution")
    print("xi: ", incXi, "kn: ", incKn, "z = ", calculate_objective_function(p, incXi, demand, beta, kioskCost, incKn, incYm, penalty))

def newSolution(xi, kn, T, beta, volume, demand, p, kioskVolume, kioskCost, incXi, incKn, penalty, f):
    
    #create temporary xi and kn values
    nxi = copy.deepcopy(xi)
    nkn = copy.deepcopy(kn)
    
    #randomly pick variable to modify
    leaving = generateLeaving(nxi)
    
    #modify kiosk selection
    if leaving == len(nxi):
        #Update kn list
        oldKiosk = leavingKiosk(nkn)
        newKiosk = newK(oldKiosk)
        nkn[oldKiosk] = 0
        nkn[newKiosk] = 1
        
        #Adjust xi values to fit volume
        currentVolume = kioskVolume[oldKiosk]
        i = 0
        if kioskVolume[oldKiosk] > kioskVolume[newKiosk]:
            while currentVolume > kioskVolume[newKiosk]:
                if nxi[i] > 0 and currentVolume - volume[i] >= kioskVolume[newKiosk] :
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
   
    #modify xi values
    else:
        add = generateAdd(leaving, nxi, volume)
        
        if volume[add]/volume[leaving] == 1:
            nxi[leaving] = nxi[leaving] - 1
            nxi[add] = nxi[add] + 1
        elif volume[add]/volume[leaving] == 2:
            nxi[leaving] = nxi[leaving] - 2
            nxi[add] = nxi[add] + 1
        else:
            nxi[leaving] = nxi[leaving] - 1
            nxi[add] = nxi[add] + 2
    
    #ensure that new solution meets constraints
    check_Constraints(nxi, nkn, volume, kioskVolume)
    
    nym = calc_ym(nxi, demand)
    ym = calc_ym(xi, demand)
    incYm = calc_ym(incXi, demand)
    
    #calculate SOS2 variables
    z_nx = calculate_SOS2_variables(f, nxi)
    z_x = calculate_SOS2_variables(f, xi)
    z_incx = calculate_SOS2_variables(f, incXi)
    z_d = calculate_SOS2_variables(f, demand)
    
    #calculate objective function
    Zn = calculate_objective_function(p, z_nx, z_d, beta, kioskCost, nkn, nym, penalty)
    Zc = calculate_objective_function(p, z_x, z_d, beta, kioskCost, kn, ym, penalty)
    
    #keep solution with lower objective value
    if Zn < Zc:
        xi = copy.deepcopy(nxi)
        kn = copy.deepcopy(nkn)
    
    #keep solution with higher objective value with some probability
    elif random.uniform(0,1) <= math.exp((Zc-Zn)/T):
        xi = copy.deepcopy(nxi)
        kn = copy.deepcopy(nkn)
        
    #if new solution has lower objective value than the incumbent, replace incumbent with new solution
    if Zn < calculate_objective_function(p, z_incx, z_d, beta, kioskCost, incKn, incYm, penalty):
        incXi = copy.deepcopy(nxi)
        incKn = copy.deepcopy(nkn)
        
    return xi, kn, incXi, incKn  

#calculate unmet demand
def calc_ym(xi, demand):
    ym = []
    for i in range(len(xi)):
        ym[i] = xi[i] - demand[i]
    return ym

#check that solution meets all constraints
def check_Constraints(testxi, testkn, volume, kioskVolume):
    #Check xi values are positive integers
    #Calculate total product volume and check for exceeding demand
    totalVolume = 0
    for i in range(len(testxi)):
        if isinstance(testxi[i], int) == False:
            print(i)
            raise RuntimeError("Error: xi value is not integer")
        if testxi[i]<0:
            print(i)
            raise RuntimeError("Error: xi value is negative")
        totalVolume = totalVolume + testxi[i]*volume[i]
    
    #Check kn values are binary
    #Calculate volume of selected kiosk and count how many kiosks are selected
    kioskCount = 0
    selectedKioskVolume = 0
    for n in range(len(testkn)):
        if testkn[n] != 0 and testkn[n] != 1:
            sys.exit("Error: kn value not binary")
        kioskCount = kioskCount + testkn[n]
        selectedKioskVolume = selectedKioskVolume + testkn[n]*kioskVolume[n]
    #Check number of kiosks selected
    if kioskCount > 1:
        sys.exit("Error: Multiple kiosks selected")
    elif kioskCount < 1:
        sys.exit("Error: No kiosk selected")
    #Check if product volume exceeds kiosk capacity
    if totalVolume > selectedKioskVolume:
        print(selectedKioskVolume, totalVolume, volume)
        sys.exit("Error: Exceeded Kiosk Volume")

#Randomly picks leaving xi value and verifies feasibility
def generateLeaving(xi):
    leaving = random.randint(0,len(xi))
    if leaving == len(xi): #not associated with any xi, change the kn value
        return leaving
    elif xi[leaving] != 0: #check if leaving value already 0
        return leaving
    else: 
        return generateLeaving(xi)

#Randomly picks incoming xi value and verifies feasibility
def generateAdd(leaving, xi, volume):
    add = random.randint(0,len(xi)-1)
    if add == leaving: # checks if incoming xi matches leaving xi
        return generateAdd(leaving, xi, volume)
    if volume[add]/volume[leaving] > 1 and xi[leaving] < 2: # checks if volume of incoming product requires more slots than leaving xi has
        return generateAdd(leaving, xi, volume)
    else: 
        return add

#determines which kiosk is leaving
def leavingKiosk(kn):
    for i in range(len(kn)):
        if kn[i] == 1:
            return i

#determines which kiosk is replacing leaving kiosk
def newK(oldKiosk):
    R = random.randint(0,2)
    if R == oldKiosk:
        return newK(oldKiosk)
    else:
        return R

#copied from Husssein's part
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


