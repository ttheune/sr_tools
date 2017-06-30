import boto3
import json
import logging
import os
import requests
import re

from base64 import b64decode
from urlparse import parse_qs

# Pull in the encrypted tokens from Lambda
ENCRYPTED_EXPECTED_TOKEN = os.environ['kmsEncryptedToken']
ENCRYPTED_ROLLER_TOKEN = os.environ['kmsEncryptedRollerToken']
# Decrypt tokens from kms to Plaintext
kms = boto3.client('kms')
expected_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']
roller_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_ROLLER_TOKEN))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Simple json response to slack
def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

# Call the roller api and pass on the json response
# See https://github.com/ttheune/sr_tools/blob/master/lambda_roller.py for details
def roll(dice, edge=None, init=None):
    base_url = 'https://api.tenminutesout.net/v1/sr_roller'
    headers = {'x-api-key':roller_token}
    data = {
        "dice":int(dice),
        "edge":bool(edge),
        "init":init
    }
    response = requests.post(base_url, headers=headers, data=json.dumps(data))
    return response.json()

# Read the text field from slack and try to clean it up
# so we can send it to the roller API
def parse_text(text):
    # initiative is handled differently, pull the number before and after the word
    # to send dice and value to the roller API
    if "init" in text:
        dice = int(re.search('^\d+',text).group(0))
        init = int(re.search('(?<=init )\d+',text).group(0))
        return roll(dice,init=init)
    # Check for edge, if it's there, send the bool to the roller API with the die pool
    elif "edge" in text:
        dice = re.search('^\d+',text).group(0)
        return roll(dice,edge=True)
    # Simplest case, just take the digits at the begining of the text and send those
    # to the roller API
    # NOTE: should check to make sure theres digits at the begining of the text always
    else:
        dice = int(re.search('^\d+',text).group(0))
        return roll(dice)

# Take the results from parse_test() and build a human friendly response to
# post in Slack.
def results(results):
    # Did we send bad data to the roller API?  Lets just stop now.
    # Oh, and no need to share with everyone else, keep it ephemeral.
    if results['err']:
            return {"text": results['err']}
    # Build the response to Slack
    output = ''
    if results['glitch'] == "Critical":
        output = "UhOh, Grit Glitch!\n"
    elif results['glitch']:
        output == "Glitch!\n"
    if results['init']:
        output += "You get %s passes at %s\n" % (results['passes'],results['init'])
    else:
        output += "You got %s hits on %s dice\n" % (results['hits'],results['dice'])
    # Return the response to the channel so everyone can see.
    return {"text":output,"response_type":"in_channel"}

# AWS Lambda tool, this is how we get data in to manipulate.
def lambda_handler(event, context):
    # Pull apart the text Slack gives us into a dict
    params = parse_qs(event['body'])
    # Grab the token and make sure we're allowed to do this.
    token = params['token'][0]
    if token != expected_token:
        logger.error("Request token (%s) does not match expected", token)
        return respond(Exception('Invalid request token'))
    # Send the text from the body to parse_text() for parsing
    # then send the output from the parser to slack
    result = results(parse_text(params['text'][0]))

    return respond(None, result)
