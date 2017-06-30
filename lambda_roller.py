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
def results(rolls, edges, init):
    # Build the result json
    result = {
        "rolls":rolls,
        "edges":edges,
        "glitch":None
    }
    dice = 0

    if edges:
        ones = rolls[0] + edges[0]
        hits = rolls[4] + rolls[5] + edges[4] + edges[5]
        for i in range(6):
            dice += rolls[i] + edges[i]
    else:
        ones = rolls[0]
        hits = rolls[4] + rolls[5]
        for i in range(6):
            dice += rolls[i]

    result["dice"] = dice

    if ones > dice/2:
        if hits == 0:
            result["glitch"] = "Critical"
        else:
            result["glitch"] = hits

    result["hits"] = hits

    if init:
        if edges:
            result = {"err":"You can not pre-edge initiative"}
            return result
        if not isinstance(init, (int)):
            result = {"err":"%s is not an integer" % init}
            return result
        if init < 0:
            result = {"err":"Positive numbers only"}
            return result
        if init > 20:
            result = {"err":"Max possible initiative score is 20"}
            return result
        if dice > 5:
            result = {"err":"Max possible initiative dice is 5"}
            return result
        d = 1
        total = 0
        for score in rolls:
            total += score * d
            d += 1
        init += total
        if init % 10 > 0:
            result["passes"] = init/10+1
        else:
            result["passes"] = init/10
        result["init"] = init
    else:
        result["passes"] = None
        result["init"] = None

    return result

def lambda_handler(event, context):
    if event["dice"]:
        if event["dice"] < 100:
            rolls = roll(event["dice"])
        else:
            result = {"err":"%s was more than 99 dice." % event["dice"]}
            return result
    else:
        rolls = roll(0)
    if event["edge"]:
        edges = edge(rolls[5])
    else:
        edges = None
    result = results(rolls, edges, event["init"])
    return result
