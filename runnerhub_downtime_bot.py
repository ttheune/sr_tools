#! /usr/bin/env python3

import datetime
import httplib2
import json
import os
import praw
import re

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

# Globals
CLIENT_ID = 'hRWYUBALsuNkSA'
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
USER_AGENT = 'python:hubdowntimebot:v.01 (by /u/og_zweiblumen)'
USER_NAME = os.environ.get('USER_NAME')
PASSWORD = os.environ.get('PASSWORD')
SUBREDDIT_NAME = os.environ.get('SUBREDDIT_NAME')
"""ENCRYPTED_ROLLER_TOKEN = os.environ['kmsEncryptedRollerToken']
kms = boto3.client('kms')
roller_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_ROLLER_TOKEN))['Plaintext']"""
roller_token = os.environ.get('ROLLER_TOKEN')


# Create reddit and subreddit objects
def get_reddit():
    reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, password=PASSWORD, user_agent=USER_AGENT, username=USER_NAME)
    subreddit = reddit.subreddit(SUBREDDIT_NAME)
    return(reddit, subreddit)


# Get downtime thread
def get_downtime(subreddit):
    thread = [submission for submission in subreddit.new(limit=5) if submission.title == 'DOWNTIME'][0]
    return thread


# Get new posts
def new_posts(thread):
    posts = [repl for repl in thread.comments.list() if repl.is_root and repl.replies.list() == []]
    return posts


# Call the roller api and pass on the json response
# See https://github.com/ttheune/sr_tools/blob/master/lambda_roller.py for details
def roll(dice, edge=None, init=None, verbose=None):
    base_url = 'https://api.tenminutesout.net/v1/sr_roller'
    headers = {'x-api-key': roller_token}
    data = {
        "dice": int(dice),
        "edge": bool(edge),
        "init": init,
        "verbose": bool(verbose)
    }
    response = requests.post(base_url, headers=headers, data=json.dumps(data))
    return response.json()


# Parse post
def parse_post(post):
    if 'DOWNTIME' in post.body:
        if 'Acquire' in post.body:
            m = re.search('Avail\(([\d]+)\) Pool\(([\d]+)\) Tries\(([\d]+)\)', post.body)
            return m.groups()
        if 'Sprite' in post.body:
            m = re.search('Level\(([\d]+)\) Pool\(([\d]+)\) Tries\(([\d]+)\)', post.body)
            return (int(m.group(1)) * 2, m.group(2), m.group(3))


# Prettyify rolls output
def pretty_rolls(rolls):
    pretty_rolls = ''
    for count in range(6):
        pretty_rolls += "[{}'s : {}] ".format(count + 1, rolls[count])
    return pretty_rolls


# Roll dice
def get_rolls(rolls):
    opp, player, tries = rolls
    responses = []
    for attempt in range(int(tries)):
        opp_res = roll(opp)
        player_res = roll(player)
        success = str(bool(player_res['hits'] > opp_res['hits']))
        responses.append('Opposition:\n\n\tHits: {}\n\tRolls: {}\n\nPlayer:\n\n\tHits: {}\n\tRolls: {}\n\nSuccess: {}'.format(
            opp_res['hits'], pretty_rolls(opp_res['rolls']),
            player_res['hits'], pretty_rolls(player_res['rolls']),
            success
        ))
        if success == 'True':
            break
    return responses


# Build reponse post
def response_post(post):
    rolls = parse_post(post)
    data = get_rolls(rolls)
    reply = '\n\n'.join(data)
    return reply


# AWS Lambda primary function
def lambda_handler(event, context):
    reddit, subreddit = get_reddit()
    thread = get_downtime(subreddit)
    posts = new_posts(thread)
    for post in posts:
        reply = response_post(post)
        post.reply(reply)


# To run locally
def main():
    reddit, subreddit = get_reddit()
    thread = get_downtime(subreddit)
    posts = new_posts(thread)
    for post in posts:
        reply = response_post(post)
        post.reply(reply)


if __name__ == '__main__':
    main()
