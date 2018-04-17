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
USER_AGENT = 'python:hubcalbot:v.01 (by /u/og_zweiblumen)'
USER_NAME = '<BOT_NAME_HERE>'
PASSWORD = os.environ.get('PASSWORD')
JOB_FLAIR = ['Help Wanted', 'Positions Filled', 'Postponed']


def main():
    reddit, subreddit = get_reddit()
    runs = get_runs(subreddit)
    for run in runs:
        data = run_data(run)


# Create reddit and subreddit objects
def get_reddit():
    reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, password=PASSWORD, user_agent=USER_AGENT, username=USER_NAME)
    subreddit = reddit.subreddit('runnerhub')
    return(reddit, subreddit)


# Get a list of runs from /r/runnerhub
def get_runs(subreddit):
    runs = [submission for submission in subreddit.new(limit=30) if submission.link_flair_text in JOB_FLAIR]
    return runs


# Get the date of the Run
def run_date(run):
    try:
        date = re.search('{.*}', run.selftext).group()
    except (RuntimeError, TypeError, NameError):
        comment = 'Parsing error, does date exist?'
        return comment
    return date


# Get data about Run needed to submit to Gcal
def run_data(run):
    data = {}
    data['status'] = run.link_flair_text
    data['date'] = run_date(run)
    data['title'] = run.title
    return data


# Check status of run and update
def run_check(run, cal_data):
    if run_date(run) not cal_date(run):
        update_cal_date(run_date(run))
    if run.link_flair_text not cal_data(run)['flair']:
        update_cal_flair(run.link_flair_text)
    if run_delete():
        cal_delete(run.id)


if __name__ == '__main__':
    main()
