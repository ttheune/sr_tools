#!/usr/bin/python

import argparse
from random import randint

parser = argparse.ArgumentParser(description='ShadowRun Dice roller')
parser.add_argument('dice', type=int, help='Number of dice to roll')
parser.add_argument('-e', '--edge', action='store_true', help='If set, exploding 6s')
parser.add_argument('-s', '--show', action='store_true', help='Show dice rolls')

# Set globals
args = parser.parse_args()
dice = args.dice
hits = 0
ones = 0
sixes = 0

# For number of dice requests sets a random number from 1-6
def roll(dice):
  count = 0
  rolls = {}
  while count < dice:
    count += 1
    rolls[count] = randint(1,6)
  return rolls

# For each 6 rolled, roll again, if it's a six, keep rolling
def edge(hits,sixes):
  rolls = []
  while sixes > 0:
    r = roll(1).values()[0]
    rolls.append(r)
    if r > 4:
      hits += 1
    if r < 6:
      sixes -= 1
  return hits,rolls

# Roll the dice!
rolls = roll(dice)
# Count results, keep track of 1s 6s and number of dice that are above a 4
for k in rolls.keys():
  if rolls[k] > 4:
    hits += 1
  if rolls[k] == 1:
    ones += 1
  if rolls[k] == 6:
    sixes += 1

# If edged, run the edge function
if args.edge:
  hits,edges = edge(hits,sixes)
else:
  edges = False

# Print results
# Check if its a glitch or crit glitch
if ones > dice/2:
  if hits == 0:
    print "Critical Glitch!!!"
  else:
    print "Glitch!!!"
# If they want to see the rolls, print them
if args.show:
  print sorted(rolls.values())
  if edges:
    print sorted(edges)
# Print hits
print "Hits: %d" % hits
