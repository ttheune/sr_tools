#!/usr/bin/python

import argparse
from random import randint

parser = argparse.ArgumentParser(description='ShadowRun Dice roller')
parser.add_argument('dice', type=int, help='Number of dice to roll')
parser.add_argument('-e', '--edge', action='store_true', help='If set, exploding 6s')
parser.add_argument('-s', '--show', action='store_true', help='Show dice rolls')

args = parser.parse_args()
dice = args.dice
hits = 0
ones = 0
sixes = 0

def roll(dice):
  count = 0
  rolls = {}
  while count < dice:
    count += 1
    rolls[count] = randint(1,6)
  return rolls

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

rolls = roll(dice)
for k in rolls.keys():
  if rolls[k] > 4:
    hits += 1
  if rolls[k] == 1:
    ones += 1
  if rolls[k] == 6:
    sixes += 1

if args.edge:
  hits,edges = edge(hits,sixes)

if ones > dice/2:
  if hits == 0:
    print "Critical Glitch!!!"
  else:
    print "Glitch!!!"
if args.show:
  print sorted(rolls.values())
  if edges:
    print sorted(edges)
print "Hits: %d" % hits
