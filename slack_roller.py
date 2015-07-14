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

# For number of dice requests sets a random number from 1-6
def roll(dice):
  count = 0
  rolls = {}
  while count < dice:
    count += 1
    rolls[count] = randint(1,6)
  return rolls

# Count results, keep track of 1s 6s and number of dice that are above a 4
def count(rolls):
  (hits,ones,sixes) = (0,0,0)
  for k in rolls.keys():
    if rolls[k] > 4: hits += 1
    if rolls[k] == 1: ones += 1
    if rolls[k] == 6: sixes += 1
  return (hits,ones,sixes)

# Special exploding 6s for edge (check for 1s as small chance of causing glitch)
def edge(hits,ones,sixes):
  rolls = []
  while sixes > 0:
    r = roll(1).values()[0]
    rolls.append(r)
    if r == 1: ones += 1
    if r > 4: hits += 1
    if r < 6: sixes -= 1
  return hits,rolls

# Check to see if they glitched
def glitch(hits,ones,dice):
  if ones > dice/2:
    if hits == 0: glitch = 'Critical Glitch'
    else: glitch = 'Glitch'
    return glitch

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
    attachment = {"fallback":"SR dice roller for slack", "color":"danger"}
    fields = []

    parser = argparse.ArgumentParser(description='ShadowRun Dice roller')
    parser.add_argument('dice', type=int, help='Number of dice to roll')
    parser.add_argument('-e', '--edge', action='store_true', help='If set, exploding 6s')
    parser.add_argument('-s', '--show', action='store_true', help='Show dice rolls')
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
        if dice < 0:
            return "We can't roll a negative number of dice"
        if dice > 100:
            return "%s is too many dice, we'll only roll 100 of them for you" % dice

        rolls = roll(dice)
        hits,ones,sixes = count(rolls)
        if roll_edge:
          hits,edges = edge(hits,ones,sixes)
          output = 'rolling with edge'
        else:
          edges = False

        glitches = glitch(hits,ones,dice)
        if glitches: result['glitch'] = glitches

        if show_roll:
          result['rolls'] = sorted(rolls.values())
          output = 'show rolling'
          if roll_edge:
            result['edge'] = sorted(edges)
            output += ' with edge'

        result['hits'] = '%s from %s dice' % (hits,dice)
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
