import json, os
from random import randint

# For number of dice returns an array of the counts
# [1s, 2s, 3s, 4s, 5s, 6s]
def roll(dice):
    counts = [0] * 6
    for i in range(dice):
        singleRoll = randint(1, 6)
        counts[singleRoll - 1] += 1
    return counts

# For number of 6s returns an array of the counts
# With exploding rolls for more 6s
# [1s, 2s, 3s, 4s, 5s, 6s]
def edge(sixes):
    counts = roll(sixes)
    for i in range(counts[5]):
        explode = edge(1)
        for j in range(6):
            counts[j] += explode[j]
    return counts

# Determine the result of the roll
def results(rolls, edges):
    result = {}
    result["rolls"] = rolls
    result["edges"] = edges
    dice = 0
    ones = rolls[0] + edges[0]
    hits = rolls[4] + rolls[5] + edges[4] + edges[5]
    for i in range(6):
        dice += rolls[i] + edges[i]

    result["dice"] = dice
    result["hits"] = hits
    if ones > dice/2:
        if hits == 0:
            result["glitch"] = "Critical"
        else:
            result["glitch"] = hits
    return result

def lambda_handler(event, context):
    rolls = roll(event["dice"])
    if event["edge"]:
        edges = edge(rolls[5])
    else:
        edges = roll(0)
    result = results(rolls, edges)
    return result
