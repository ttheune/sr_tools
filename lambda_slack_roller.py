import boto3
import json
import logging
import os
import requests
import re

from base64 import b64decode
from urlparse import parse_qs

ENCRYPTED_EXPECTED_TOKEN = os.environ['kmsEncryptedToken']
ENCRYPTED_ROLLER_TOKEN = os.environ['kmsEncryptedRollerToken']

kms = boto3.client('kms')
expected_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_EXPECTED_TOKEN))['Plaintext']
roller_token = kms.decrypt(CiphertextBlob=b64decode(ENCRYPTED_ROLLER_TOKEN))['Plaintext']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def roll(dice, edge=None, init=None):
    base_url = 'https://api.tenminutesout.net/v1/sr_roller'
    headers = {'x-api-key':roller_token}
    data = {
        "dice":int(dice),
        "edge":edge,
        "init":init
    }
    response = requests.post(base_url, headers=headers, data=json.dumps(data))
    return response.json()

def parse_text(text):
    if "init" in text:
        dice = int(re.search('^\d+',text).group(0))
        init = int(re.search('(?<=init )\d+',text).group(0))
        return roll(dice,init=init)
    elif "edge" in text:
        dice = re.search('^\d+',text).group(0)
        return roll(dice,edge=True)
    else:
        dice = int(re.search('^\d+',text).group(0))
        return roll(dice)

def results(res):
    output = ''
    if res['glitch'] = "Critical":
        output = "UhOh, Grit Glitch!\n"
    elif res['glitch']:
        output = "Glitch!\n"
    if res['init']:
        output += "You get %s passes at %s" % (res['passes'],res['init'])
    else:
        output += "You got %s hits on %s dice" % (res['hits'],res['dice'])

def lambda_handler(event, context):
    params = parse_qs(event['body'])
    token = params['token'][0]
    if token != expected_token:
        logger.error("Request token (%s) does not match expected", token)
        return respond(Exception('Invalid request token'))

    response = {
        "text":"%s" % parse_text(params['text'][0]),
        "response_type":"in_channel"
    }

    return respond(None, response)
