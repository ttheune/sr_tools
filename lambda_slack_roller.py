import boto3
import json
import logging
import os
import re
import requests

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
def roll(dice, edge=None, init=None, verbose=None):
    base_url = 'https://api.tenminutesout.net/v1/sr_roller'
    headers = {'x-api-key':roller_token}
    data = {
        "dice":int(dice),
        "edge":bool(edge),
        "init":init,
        "verbose":bool(verbose)
    }
    response = requests.post(base_url, headers=headers, data=json.dumps(data))
    return response.json()

# Read the text field from slack and try to clean it up
# so we can send it to the roller API
def parse_text(text):
    # Usage information
    usage = "Usage: /roll <dice> [edge|init <score>|verb]\n"
    usage += "'edge' 'init' and 'verb' are optional, with 'edge' and 'init'\n"
    usage += "being mutually exclusive.\n"
    usage += "<dice> and <score> must be numbers.\n"
    usage += "<dice> must be between 0 and 99.\n"
    usage += "<score> must be between 1 and 20.\n"
    usage += "'verb' will give verbose results showing die rolls."

    # Get the number of dice, and make sure the first field is an int
    try:
        dice = int(re.search('^\d+',text).group(0))
    except:
        output = "Request did not begin with a number.\n"
        return {'err':output + usage}

    # initiative is handled differently, pull the number before and after the word
    # to send dice and value to the roller API
    if "init" in text:
        try:
            init = int(re.search('(?<=init )\d+',text).group(0))
        except:
            output = "Tried to roll init without an initiative score.\n"
            return {'err':output + usage}
        if "verb" in text:
            return roll(dice,init=init,verbose=True)
        else:
            return roll(dice,init=True)

    # Check for edge, if it's there, send the bool to the roller API with the die pool
    elif "edge" in text:
        if "verb" in text:
            return roll(dice,edge=True,verbose=True)
        else:
            return roll(dice,edge=True)

    # Simplest case, just take the digits at the begining of the text and send those
    # to the roller API regardless of what else follows.
    else:
        if "verb" in text:
            return roll(dice,verbose=True)
        else:
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
    if results['verbose']:
        for c in range(6):
            output += ":die_%s: %s " % (c+1,results['rolls'][c])

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
