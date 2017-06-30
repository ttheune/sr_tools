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
        "glitch":None,
        "err":None
    }
    dice = 0
    # Calculate number of 4's and 5's for hits
    # and 1's to check for glitches
    ones = rolls[0] if not edges else rolls[0] + edges[0]
    hits = rolls[4] + rolls[5] if not edges else rolls[4] + rolls[5] + edges[4] + edges[5]
    for i in range(6):
        dice += rolls[i] if not edges else rolls[i] + edges[i]
    # Set the total number of dice rolled
    # this is to more easily calculate glitches as
    # well as returning to the user how many more
    # dice were rolled if they used Edge
    result["dice"] = dice
    # Check for a Crit Glitch or regular Glitch
    if ones > dice/2:
        if hits == 0:
            result["glitch"] = "Critical"
        else:
            result["glitch"] = hits
    # Always return how many total hits, even if we don't use them
    result["hits"] = hits
    # Calculating initiative is completely different, but we still
    # use 6 sided dice to figure it out, we just don't care about
    # hits and need to sum the values of the dice instead.
    # Also, there are are more limits on the number of dice and the
    # value your base initiative can be.
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
    # Return a json string with a base of:
    # {"passes": null, "hits": 0, "dice": 0, "err": null, "glitch": null, "init": null, "edges": null, "rolls": [0, 0, 0, 0, 0, 0]}
    return result

# AWS Lambda tool, this is how we get data in to manipulate.
def lambda_handler(event, context):
    # Input is {'dice':null|int,'edge':bool,'init':null|int}
    # Lets make sure we aren't trying to randomize the universe,
    # keep it to two digits of dice
    if event["dice"]:
        if event["dice"] < 100:
            rolls = roll(event["dice"])
        else:
            result = {"err":"%s was more than 99 dice." % event["dice"]}
            return result
    else:
        rolls = roll(0)
    # Pre-edging in ShadowRun means you get to re-roll 6s.
    # But they explode, so we've another function special for them.
    if event["edge"]:
        edges = edge(rolls[5])
    else:
        edges = None

    # Pass on the output from results() to the user
    return results(rolls, edges, event["init"])
