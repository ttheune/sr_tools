#import argparse
from random import randint
from flask import Flask
from flask import request
import json, os
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
    output = 'rolling'
    url = '<slack webhook url>'
    text = ''
    payload = {}
    payload['icon_emoji'] = ':game_die:'
    payload['channel'] = '#test'

    if request.method == 'POST':
        if request.form['token'] != '<slack token>':
          return 'Not Slack :('
        user = request.form['user_name']
        payload['username'] = user
        req = request.form['text'].split()

        if len(req) > 3: return 'Too many fields'
        for opt in req:
            if opt == 'edge': roll_edge = True
            elif opt == 'show': show_roll = True
            else: dice = int(opt)

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

        result['hits'] = hits
        for k,v in result.iteritems():text += "%s: %s " % (k,v)
        payload['text'] = text
        payload = json.dumps(payload)
        command = "curl -X POST --data-urlencode 'payload=%s' %s" % (payload,url)
        os.system(command)
            
        print result
        return output
    else:
        return 'No POST'
        
if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=True, debug=True)
