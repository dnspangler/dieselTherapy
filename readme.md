#Diesel Therapy

The year is 2021, and The Making Healthcare Great Again Act has recently opened up exciting new opportunities in the field of pre-hospital care. As an up-and-coming private ambulance service provider, your goal is to make as much money as you can. Watch out though - If you kill too many patients the pesky government might try and regulate you again!

Run game.py to play. Press the 'm' key and hit enter your keyboard to play a game manually,  or use the 's' key simulate a game based on parameters set in the source code. 

Your ambulance starts at the hospital at the origin of an (x,y) plane, with a patient spawned somewhere near you. New patients will spawn randomlyas the game progresses. Move to them with the (wasd) keys, (l)ad them ontoyour, drive them back to the hospital at the origin, where you can (u)nload them. 

At the end of the turn, you will get paid cash money for any unloaded patients at the hospital. But watch out - Any patients not
at the hospital will deteriorate! A patient whose deterioration exeecedstheir satbility will die, and you will be fined a hefty sum. 

To prevent this, (t)reat your loaded patients - a d6 roll of 4+ modified by the difference between the treatment skill of your ambulance and the difficulty score of the patient, results in the deterioration of the patient being reduced by 1. (t)reating a patient with 0 deterioration implies successfully treating them in the field, and you get paid without having to lug them tothe Emergency Department - a failed check means a dead patient though!

Stressful events such as having a patient die will stress crews out, and if a crew's stress exceeds it's chill, speed will be reduced. Let your crews (c)hill for a full turn to recover from stress.