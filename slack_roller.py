'''
You will need to replace the values for:
url
request.form['token']
and create the channel #shadowrun
'''

#import argparse
from random import randint
from flask import Flask
from flask import request
import json, os, argparse
app = Flask(__name__)

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
    counts = [0] * 6
    for i in range(sixes):
        singleRoll = randint(1, 6)
        counts[singleRoll - 1] += 1
        if singleRoll == 6: 
            explode = edge(1)
            for j in range(0, 5):
                counts[j] += explode[j]
    return counts

# Determine the result of the roll
def results(rolls, edges):
    dice = 0
    ones = rolls[0] + edges[0]
    hits = rolls[4] + rolls[5] + edges[4] + edges[5]
    for i in range(0, 5):
        dice += rolls[i] + edges[i]
    if ones > dice/2:
        if hits == 0: 
            result = 'Critical Glitch'
        else:
            result = 'Glitch with ' + str(hits) + ' hits'
    else:
        result = str(hits) + ' hits'
    return result

@app.route('/roll', methods=['POST', 'GET'])
def req():
    # Set globals
    roll_edge = False
    show_roll = False
    result = {}
    attachments = []
    output = 'rolling'
    url = '<slack webhook url>'
    text = ''
    payload = {}
    payload['icon_emoji'] = ':game_die:'
    payload['channel'] = '#shadowrun'
    payload['attachments'] = []
    attachment = {"fallback":"SR dice roller for slack", "color":"danger", "mrkdwn_in": ["fields"]}
    fields = []

    parser = argparse.ArgumentParser(description='ShadowRun Dice roller')
    parser.add_argument('dice', type=int, help='Number of dice to roll')
    parser.add_argument('-e', '--edge', action='store_true', help='If set, exploding 6s')
    parser.add_argument('-s', '--show', action='store_true', help='Show dice rolls')
    parser.add_argument('-i', '--invis', action='store_true', help='Hide die pool')
    parser.add_argument('msg', nargs='*')

    if request.method == 'POST':
        if request.form['token'] != '<slack token>':
            return 'Not Slack :('
        user = request.form['user_name']
        payload['username'] = user
        req = request.form['text'].split()
        try:
            args = parser.parse_args(req)
        except:
            return "Parse error.\nUsage: /roll [-s] [-e] dice [message]"
        dice = args.dice
        if args.edge: roll_edge = True
        if args.show: show_roll = True
        if args.msg: result['message'] = ' '.join(args.msg)
        if not args.invis: result['dice'] = dice
        if dice < 0:
            return "We can't roll a negative number of dice"
        if dice > 100:
            return "%s is too many dice, we'll only roll 100 of them for you" % dice

        rolls = roll(dice)
        if roll_edge:
            edges = edge(rolls[5])
            output = 'rolling with edge'
        else:
            edges = [0] * 6

        result['outcome'] = results(rolls, edges)
        
        verbose = ''
        if show_roll:
            output = 'show rolling'
            first = '```\n'
            keys = '| pips | rolls |'
            divider = '+------+-------+'
            data = [''] * 6
            for i in range(6):
                data[i] = '|   ' + str(i+1) + '  | ' + (' ' * (5-len(str(rolls[i])))) + str(rolls[i]) + ' |'
            last = '```\n'
            if roll_edge:
                keys += ' edges |'
                divider += '-------+'
                for i in range(6):
                    data[i] = data[i] + ' ' + (' ' * (5-len(str(edges[i])))) + str(edges[i]) + ' |'
            divider += '\n'
            verbose = first + divider + keys + '\n' + divider
            for i in range(6):
                verbose += data[i] + '\n' + divider
            verbose += last
            result['verbose'] = verbose


        for k,v in result.iteritems():
            field = {"title":k,"value":str(v),"short":True}
            fields.append(field)
            text += "%s: %s\n" % (k,v)
        attachment['fields'] = fields
        attachments.append(attachment)
        payload['attachments'] = attachments
        payload = json.dumps(payload)
        command = "curl -X POST --data-urlencode 'payload=%s' %s" % (payload,url)
        os.system(command)
        print payload
        return 'ok'
    else:
        return 'No POST'
        
if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True, debug=True)
