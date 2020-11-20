import sys
import random
import copy
from copy import deepcopy
import math

#Decision Variables
######0,1,2,3,4,5,6,7,8,9,10,11,12,13
xi = [4,6,5,3,1,20,1,1,1,6,0,0,0,0]
kn = [0,1,0]

#Parameters
alpha = 10

volume = [1,1,1,1,1,1,1,1,1,1,1,1,1,2] #volume must be 1 or 2 spaces
demand = [4,6,5,3,1,20,1,1,1,10,1,5,5,20]
profit = [8.75,8.75,8.75,40,20,2,10,10,30,5,10,7,15,8]

kioskVolume = [24,48,60]
kioskCost = [4399,5999,10999]

#Checks that a solution meets all constraints and throws errors if it doesn't
def check_Constraints(testxi, testkn):
    #Check xi values are positive integers
    #Calculate total product volume and check for exceeding demand
    totalVolume = 0
    for i in range(len(testxi)):
        if isinstance(testxi[i], int) == False:
            print(i)
            sys.exit("Error: xi value is not integer")
        if testxi[i]<0:
            print(i)
            sys.exit("Error: xi value is negative")
        if testxi[i] > demand[i]:
            print(i, testxi, demand [i])
            sys.exit("Error: xi value exceeded demand")
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
        
    print("Meets all constraints")

#Calculates z for a given set of xi and kn values
def calc_z(calcxi, calckn):
    z = 0
    for i in range(len(calcxi)):
        z = z + calcxi[i]*profit[i]
    for n in range(len(calckn)):
        z = z - (1/alpha)*calckn[n]*kioskCost[n]
    return z

#Randomly picks leaving xi value and verifies feasibility
def generateLeaving():
    leaving = random.randint(0,len(xi))
    if leaving == len(xi): #not associated with any xi, change the kn value
        return leaving
    elif xi[leaving] != 0: #check if leaving value already 0
        return leaving
    else: 
        return generateLeaving()

#Randomly picks incoming xi value and verifies feasibility
def generateAdd(leaving):
    add = random.randint(0,len(xi)-1)
    if xi[add] + math.ceil(volume[leaving]/volume[add]) >= demand[add]:  # checks if xi already at max value
        return generateAdd(leaving)
    if add == leaving: # checks if incoming xi matches leaving xi
        return generateAdd(leaving)
    if volume[add]/volume[leaving] > 1 and xi[leaving] < 2: # checks if volume of incoming product requires more slots than leaving xi has
        return generateAdd(leaving)
    else: 
        return add

def leavingKiosk():
    for i in range(len(kn)):
        if kn[i] == 1:
            return i

def newK(oldKiosk):
    R = random.randint(0,2)
    if R == oldKiosk:
        return newK(oldKiosk)
    else:
        return R

def newSolution():
    global xi
    global kn
    global incKn
    global incXi
    
    #create temporary xi and kn values
    tempxi = copy.deepcopy(xi)
    tempkn = copy.deepcopy(kn)
    
    #randomly pick variable to modify
    leaving = generateLeaving()
    
    #modify kiosk selection
    if leaving == len(tempxi):
        #Update kn list
        oldKiosk = leavingKiosk()
        newKiosk = newK(oldKiosk)
        tempkn[oldKiosk] = 0
        tempkn[newKiosk] = 1
        
        #Adjust xi values to fit volume
        currentVolume = kioskVolume[oldKiosk]
        i = 0
        if kioskVolume[oldKiosk] > kioskVolume[newKiosk]:
            while currentVolume > kioskVolume[newKiosk]:
                if tempxi[i] > 0 and currentVolume - volume[i] >= kioskVolume[newKiosk] :
                    tempxi[i] = tempxi[i] - 1
                    currentVolume = currentVolume - volume[i]
                if i < len(tempxi) - 1:
                    i = i + 1
                else:
                    i = 0
        if kioskVolume[oldKiosk] < kioskVolume[newKiosk]:
            while currentVolume < kioskVolume[newKiosk]: 
                if tempxi[i] + 1 <= demand[i] and currentVolume + volume[i] <= kioskVolume[newKiosk]:
                    tempxi[i] = tempxi[i] + 1
                    currentVolume = currentVolume + volume[i]
                if i < len(tempxi) - 1:
                    i = i + 1
                else:
                    i = 0
   
    #modify xi values
    else:
        add = generateAdd(leaving)
        
        if volume[add]/volume[leaving] == 1:
            tempxi[leaving] = tempxi[leaving] - 1
            tempxi[add] = tempxi[add] + 1
        elif volume[add]/volume[leaving] == 2:
            tempxi[leaving] = tempxi[leaving] - 2
            tempxi[add] = tempxi[add] + 1
        else:
            tempxi[leaving] = tempxi[leaving] - 1
            tempxi[add] = tempxi[add] + 2
   
    print("Suggested Solution")
    print("xi: ", tempxi, "kn: ", tempkn, "z = ", calc_z(tempxi, tempkn))
    
    check_Constraints(tempxi, tempkn)
    
    if calc_z(tempxi, tempkn) > calc_z(xi, kn):
        xi = copy.deepcopy(tempxi)
        kn = copy.deepcopy(tempkn)



#Main
print("Initial Solution")
print("xi: ", xi, "kn: ", kn, "z = ", calc_z(xi, kn))

for i in range(200):
    newSolution()
    print(i)

print("Final Solution")
print("xi: ", xi, "kn: ", kn, "z = ", calc_z(xi, kn))

