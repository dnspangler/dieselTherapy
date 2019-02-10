import os
import pandas as pd
import numpy as np
import time

# Set global game variables

nturns = 5
marketsize = 5
ptChance = 0.2

# Simulation configurations

simTxRisk = 2 # Maximum difference in treatment skill and pt difficulty that AI will try to treat
simStress = 1 # Maximum amount of stress AI will allow before resting

# Base ambulance properties

ambxy = (0,0)
ambspd = 4
ambtx = 4
ambcap = 1
ambstress = 0
ambchill = 2

# Base patient properties

ptxyrange = (-5,5)
ptstage = "map" # 0 = EMD, 1 = ptContact, 2 = ED Queue, 3 = Treated, 4 = Dead
ptpriorange = (1,3)
ptpriostabmult = 2
ptstabrange = (0,10)
ptstabsd = 2
ptpaymod = (0,100)
pttype = ["cardiac","pediatric","stroke","sick","trauma","diffbr"]

# Define items

itemdf = pd.read_csv('items.csv')

# Define game classes

class Item:
    
    def __init__(self,uid):
        self.uid = uid
        self.name = list(itemdf.loc[itemdf.uid == uid,'name'])[0]
        self.type = list(itemdf.loc[itemdf.uid == uid,'type'])[0]
        self.prop = list(itemdf.loc[itemdf.uid == uid,'prop'])
        self.mod = list(itemdf.loc[itemdf.uid == uid,'mod'])
        self.cond = list(itemdf.loc[itemdf.uid == uid,'cond'])
        self.cost = list(itemdf.loc[itemdf.uid == uid,'cost'])[0]
        self.upkeep = list(itemdf.loc[itemdf.uid == uid,'upkeep'])[0]
        self.text = list(itemdf.loc[itemdf.uid == uid,'text'])[0]

    def summary(self):
        print("itemuid:",self.uid,
              "name:",self.name,
              "type:",self.type,
              "prop:",self.prop,
              "mod:",self.mod,
              "cond:",self.cond,
              "cost:",self.cost,
              "upkeep:",self.upkeep)

class Amb:
    uid = -1
    
    def __init__(self):
        Amb.uid += 1
        self.uid = Amb.uid
        self.xy = ambxy
        self.pts = []
        self.items = []
        self.relax = 0
        self.spd = ambspd
        self.moves = ambspd
        self.tx = ambtx
        self.stress = ambstress
        self.chill = ambchill
        self.cap = ambcap
        self.simTarget = -1
    
    def moveAmb(self,dxy):
            self.xy = (self.xy[0]+dxy[0],
                       self.xy[1]+dxy[1])
            self.moves -= 1
            for i in self.pts:
                game["ptList"][i].movePt(dxy)
            print(self.uid,"xy:",self.xy)
    
    def treatPt(self,ptuid):
        d6 = np.random.uniform(1,6)
        mod = self.tx - game["ptList"][ptuid].diff
        self.moves -= 1
        if game["ptList"][ptuid].det <= 0 and game["ptList"][ptuid].stage == "loaded":
            if d6 + mod > 3:
                game["ptList"][ptuid].stage = "treated"
                game["cash"] += game["ptList"][ptuid].pay
                print("Patient",ptuid,"treated for",game["ptList"][ptuid].pay)
                self.pts.remove(ptuid)
            else:
                game["ptList"][ptuid].stage = "dead"
                self.stress += 1
                fine = game["ptList"][ptuid].pay + ptpaymod[1]
                game["cash"] -= fine
                print("You just killed patient",ptuid,", son! Fined",fine)
                self.pts.remove(ptuid)
        else:
            if d6 + mod > 3:
                game["ptList"][ptuid].det = max(0,game["ptList"][ptuid].det - 1)
                print("Patient",ptuid,"stabilized to",game["ptList"][ptuid].det)
            else:
                print("Failed to stabilize patient",ptuid)
    
    
    def resetTurn(self):
        self.moves = self.spd
        if self.relax == self.spd and self.stress > 0:
            self.stress -= 1
        self.moves -= max([0,self.stress - self.chill])
        self.relax = 0
        self.summary()
    
    def summary(self):
        print("ambid:",self.uid,
              "xy:",self.xy,
              "moves:",self.moves,
              "stress:",self.stress,
              "chill:",self.chill,
              "tx:",self.tx,
              "cap:",self.cap,
              "pts:",self.pts,
              "items:",self.items)

class Pt:
    uid = -1
    
    def __init__(self):
        Pt.uid += 1
        self.uid = Pt.uid
        self.stage = ptstage
        self.xy = (round(np.random.uniform(ptxyrange[0],
                                           ptxyrange[1])),
                   round(np.random.uniform(ptxyrange[0],
                                           ptxyrange[1])))
        self.prio = round(np.random.uniform(ptpriorange[0],
                                            ptpriorange[1]))
        self.type = pttype[int(np.random.uniform(0,len(pttype)))-1]
        self.stab = ptstabfun(self)
        self.diff = ptstabrange[1] - ptstabfun(self)
        self.det = 0
        self.amb = -1
        self.pay = ((ptstabrange[1] - self.stab) * self.diff) + round(np.random.uniform(ptpaymod[0],ptpaymod[1]))
    
    def movePt(self,dxy):
        self.xy = (self.xy[0] + dxy[0],
                   self.xy[1] + dxy[1])
        
    def resetTurn(self):
        if len(game["edQueue"]) > 0:
            if game["edQueue"][0] == self.uid:
                self.stage = "treated"
                game["cash"] += self.pay
                game["edQueue"].pop(0)
                print("Patient",self.uid,"treated for", self.pay)
                self.summary()
        elif self.stage in ["map","loaded","edQueue"]:
            self.det += 1
            if self.det > self.stab:
                self.stage = "dead"
                game["cash"] -= self.pay
                if self.amb >= 0:
                    game["ambList"][self.amb].stress += 1
                    game["ambList"][self.amb].pts.remove(self.uid)
                print("Patient",self.uid,"died, bro!")
            self.summary()
        
    
    def summary(self):
        print('ptid:',self.uid,
        "xy:",self.xy,
        "stage:",self.stage,
        "prio:",self.prio,
        "type:",self.type,
        "stab:",self.stab,
        "diff:",self.diff,
        "det:",self.det,
        "pay:",self.pay,
        "amb:",self.amb)
        
        
# Define game functions

def ptstabfun(P):
    c = round(np.random.normal(P.prio * ptpriostabmult,ptstabsd))
    while ptstabrange[0] >= c or c >= ptstabrange[1] :
        c = round(np.random.normal(P.prio * ptpriostabmult,ptstabsd))
    return(c)

def getNearestPt(A,game):
    lowid = -1
    lowdxy = 100
    if len(game["ptList"]) > 0:
        for i in game["ptList"]:
            dxy = abs(i.xy[0] - A.xy[0]) + abs(i.xy[1] - A.xy[1])
            simTarget = i.uid in [i.simTarget for i in game["ambList"]]
            if lowdxy > dxy and i.stage == "map" and simTarget == False:
                lowid = i.uid
                lowdxy = abs(i.xy[0] - A.xy[0]) + abs(i.xy[1] - A.xy[1])
    return([lowid,lowdxy])
        
            
def userAction(A,game):
    
    nearpt = getNearestPt(A,game)

    print(A.moves,"actions: (wasd)move  (c)hill  (l)oad  (u)nload  (t)reat  (r)ush (i)tems  new (p)t  (g)amestate  (e)nd")
    
    act = input()
    
    action(act,A,game,nearpt)

def simAction(A,game):
    
    nearpt = getNearestPt(A,game)

    if(not "map" in [i.stage for i in game["ptList"]]):
        act = "c"
    if(A.stress > simStress and A.moves + A.relax == A.spd):
        act = "c"
    elif(len(A.pts)<1): # Maybe update this to hande txp of multiple pts
        if(A.xy[0]>game["ptList"][nearpt[0]].xy[0]):
            act = "a"
        elif(A.xy[0]<game["ptList"][nearpt[0]].xy[0]):
            act = "d"
        elif(A.xy[1]>game["ptList"][nearpt[0]].xy[1]):
            act = "s"
        elif(A.xy[1]<game["ptList"][nearpt[0]].xy[1]):
            act = "w"
        elif game["ptList"][nearpt[0]].stage == "map":
            act = "l"
    elif(game["ptList"][A.pts[0]].det >= game["ptList"][A.pts[0]].stab & game["ptList"][A.pts[0]].diff < A.tx + simTxRisk):
        act = "t"
    elif(A.xy[0]>ambxy[0]):
            act = "a"
    elif(A.xy[0]<ambxy[0]):
        act = "d"
    elif(A.xy[1]>ambxy[1]):
        act = "s"
    elif(A.xy[1]<ambxy[1]):
        act = "w"
    else:
        act = "u"
    
    print(act)
    action(act,A,game,nearpt)
    
    
def action(action,A,game,nearpt):
    if action == "w":
        A.moveAmb((0,1))
    elif action == "a":
        A.moveAmb((-1,0))
    elif action == "s":
        A.moveAmb((0,-1))
    elif action == "d":
        A.moveAmb((1,0))
    elif action == "c":
        A.relax += 1
        A.moves -= 1
    elif action == "i":
        print("Market:")
        for i in game["market"]:
            i.summary()
        print("Hand:")
        for i in game["hand"]:
            i.summary()
        for i in game["ambList"]:
            print("Ambulance" + str(i.uid) +":")
            for j in i.items:
                j.summary()
        itemnum = input("Item number to buy/use")
        if type(itemnum) == 'int':
            if int(itemnum) in range(1,marketsize):
                ambnum = input("Ambulance number/other for hand")
                if type(ambnum) == 'int':
                    if int(ambnum) in [i.uid for i in game["ambList"]]:
                        game["ambList"][int(ambnum)].items.append(game["market"].pop(int(itemnum)))
                        game["market"].append(game["deck"].pop())
        else:
            print("Whatever, dude.")
    elif action  == "l":
        if nearpt[1] == 0:
            game["ptList"][nearpt[0]].amb = A.uid
            game["ptList"][nearpt[0]].stage = "loaded"
            A.pts.append(nearpt[0])
            A.moves -= 1
            print("Patient",nearpt[0],"loaded")
        else:
            print("No patients here, bub!")
            time.sleep(1)
    elif action  == "u":
        if len(A.pts) > 0:
            if A.xy == ambxy:
                game["ptList"][A.pts[0]].stage = "edQueue"
                print("Patient",A.pts[0],"unloaded at ED")
                game["edQueue"].append(A.pts.pop())
            else:
                game["ptList"][A.pts[0]].stage = "map"
                print("Patient",A.pts[0],"unloaded")
            A.moves -= 1
            
        else:
            print("No patients loaded, man!")	
            time.sleep(1)
    elif action == "t":
        if len(A.pts) > 0:
            A.treatPt(ptuid = A.pts[0])
        else:
            print("No loaded patients, pal!") 
            time.sleep(1)
    elif action == "r":
        A.moves += 1
        A.stress += 1
    elif action == "p":
        game["ptList"].append(Pt())
    elif action == "b":
        game["ambList"].append(Amb())
    elif action == "g":
        print("Turn:",game["turn"],"Cash:",game["cash"])
        for i in game["ambList"]:
            i.summary()
        for i in game["ptList"]:
            i.summary()
    elif action == "e":
        if input("Enter to exit, ask nice to cancel") == "":
            game["turn"] = nturns
            for i in game["ambList"]:
                i.moves = 0
            return()
    else:
        print("What?")
        time.sleep(1)

# New game setup

t = "huh"
while(t not in ["m","s"]):
    print("Shall we play a game of Diesel Therapy? (m)anual, (s)imulated, (w)hat?")
    t = input()
    if(t=="w"):
        print("""
The year is 2021, and The Making Healthcare Great Again Act has recently 
opened up exciting new opportunities in the field of pre-hospital care. 
As an up-and-coming private ambulance service provider, your goal is to 
make as much money as you can. Watch out though - If you kill too many 
patients the pesky government might try and regulate you again!

Press the 'm' key and hit enter your keyboard to play a game manually, 
or use the 's' key simulate a game based on parameters set in the source 
code. 

Your ambulance starts at the hospital at the origin of an (x,y) plane, 
with a patient spawned somewhere near you. New patients will spawn randomly
as the game progresses. Move to them with the (wasd) keys, (l)ad them onto
your, drive them back to the hospital at the origin, where you can 
(u)nload them. 

At the end of the turn, you will get paid cash money for 
any unloaded patients at the hospital. But watch out - Any patients not
at the hospital will deteriorate! A patient whose deterioration exeeceds
their satbility will die, and you will be fined a hefty sum. 

To prevent this, (t)reat your loaded patients - a d6 roll of 4+ modified 
by the difference between the treatment skill of your ambulance and the 
difficulty score of the patient, results in the deterioration of the patient 
being reduced by 1. (t)reating a patient with 0 deterioration implies successfully
treating them in the field, and you get paid without having to lug them to
the Emergency Department - a failed check means a dead patient though!

Stressful events such as having a patient die will stress crews out, and 
if a crew's stress exceeds it's chill, speed will be reduced. Let your 
crews (c)hill for a full turn to recover from stress.

To do: 
-Implement functionality for items
-Make simulation smarter
""")
print("Number of turns?")
nturns = input()
nturns = int(nturns)

game = {"turn" : 0, 
        "cash" : 0,
        "deck" : [],
        "market" : [],
        "hand" : [],
        "ambList" : [],
        "ptList" : [],
        "edQueue" : []}

game["ambList"].append(Amb())
game["ambList"].append(Amb())
game["ptList"].append(Pt())
game["ptList"].append(Pt())

for i in game["ambList"]:
    i.summary()
for i in game["ptList"]:
    i.summary()

for i in range(0,max(itemdf.uid)+1):
    item = itemdf.loc[itemdf.uid == i,]
    for j in range(1,max(item.n)+1):
        game["deck"].append(Item(i))

np.random.shuffle(game["deck"])

game["market"] = game["deck"][0:marketsize]
game["deck"] = game["deck"][marketsize:-1]

# Main game loop

while game["turn"] <= nturns:
    print("Turn",game["turn"],"start,",game["cash"],"cash")
    for i in game["ambList"]:
        print("Ambulance",i.uid)
        while i.moves > 0:
            if t == "m":
                userAction(i,game)
            else:
                simAction(i,game)
    else:
        game["turn"] += 1
        for i in game["ambList"]:
            i.resetTurn()
        for i in game["ptList"]:
            i.resetTurn()
        if np.random.uniform(0,1) < ptChance:
            game["ptList"].append(Pt())
    
else:
    print("Game over, man!")
    print("Turn:",game["turn"],"Cash:",game["cash"])
    for i in game["ambList"]:
        i.summary()
    for i in game["ptList"]:
        i.summary()