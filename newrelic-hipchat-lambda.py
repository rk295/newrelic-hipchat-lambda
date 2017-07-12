#!/usr/bin/env bash
import logging
from hypchat import HypChat
import os
import json
import requests  # Needed for exceptions
import pystache
import re

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(funcName)s:%(lineno)d %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

logger.info("Starting")

html_template = "alert-template.html"


def lambda_handler(event=None, context=None):

    logger.debug("incoming event=%s" % json.dumps(event))

    body = json.loads(event['body'])
    logger.debug("incoming event body=%s" % json.dumps(body))

    # Body of the lambda response
    response = {
        "isBase64Encoded": "false",
        "statusCode": 200,
        "body": "lamba yo!"
    }

    # This is the basic format for the card we post to Hipchat. Most of this
    # is boiler plate, so its just held here.
    card = {
        "style": "application",
        "description": {
            "format": "html",
            "value": ""
        },
        "url": "https://newrelic.com",
        "format": "medium",
        "id": "db797a68-0aff-4ae8-83fc-2e72dbb1a707",
        "title": "New Relic Notification",
        "icon": {
            "url": "https://d2.alternativeto.net/dist/icons/new-relic_79903.png?width=128&height=128&mode=crop&upscale=false"
        },
        "attributes": []
    }

    # Get all these from env vars set inside the lambda job.
    hipchat_server = os.getenv('HIPCHAT_URL') or None
    token = os.getenv('TOKEN') or None

    # We can't continue without these, so error if they are blank
    if hipchat_server is None or token is None:
        err_msg = "You must set the HIPCHAT_URL and TOKEN environment variables"
        return error_response(err_msg, response)

    try:
        with open(html_template, 'r') as myfile:
            template = myfile.read().replace('\n', '')
    except:
        err_msg = "Failed to read the template file %s" % html_template
        return error_response(err_msg, response)

    hipchat = HypChat(token, endpoint=hipchat_server)

    room_id = body.get("hipchat_room")

    if room_id is None:
        err_msg = "No hipchat_room found in body, cannot continue"
        return error_response(err_msg, response, 500)

    try:
        nr_room = hipchat.get_room(room_id)
    except requests.exceptions.RequestException as e:
        err_msg = "Error occured while talking to Hipchat: " + \
            str(e)
        return error_response(err_msg, response)

    # Build up all the bits for both the card and the HTML template
    severity = body["severity"]

    if severity == "CRITICAL":
        colour = "red"
    elif severity == "WARN":
        colour = "yellow"
    elif severity == "INFO":
        colour = "green"
    else:
        colour = "gray"

    # Also support the case where we derive the severity from
    # the condition_name field.

    match = re.match( r'.*-(\w*)$', body["condition_name"])

    if match:
        if match.group(1) == "error":
            logger.debug("Detected a error condition in the condition_name field")
            colour = "red"
            body["severity"] = "ERROR"
        elif match.group(1) == "warn":
            logger.debug("Detected a warn condition in the condition_name field")
            body["severity"] = "WARNING"
            colour = "yellow"

    # The targets object in the payload is actually a list, however
    # after much testing, I've never been able to produce an alert
    # with more than a single item in it, if somebody shows me an
    # example with >1 items, I'll handle the case. But until then,
    # I'm treating that as a never seen edge case!
    incident_data = body["targets"][0]["link"]

    # Bit hacky, pushing this back into the top level of the body object
    # to make the pystache rendering easier
    body["incident_data"] = incident_data

    # Description kept short, most of the data is in the attributes
    description = "Click <a href='%s'><b>here</b></a> to acknowledge, or <a href='%s'><b>here</b></a> to view the data about this alert" % (
        body["incident_acknowledge_url"], incident_data)

    # Push the description into the card object
    card["description"]["format"] = "html"
    card["description"]["value"] = description

    # render the fall back html template
    hipchat_message = pystache.render(template, body)

    logger.debug("Message contents = %s" % hipchat_message)

    # This is the list of attributes we pull out of the payload. If you
    # want others, you can add them here.
    attribute_list = ["details", "severity",
                      "current_state", "account_name", "condition_name", "policy_name"]

    for attr in attribute_list:
        attr_dict = {}
        # I do this to make them more readable
        attr_dict["label"] = attr.replace("_", " ").title()
        attr_dict["value"] = {}
        attr_dict["value"]["label"] = body[attr]

        # Add a lozenge to the severity field. Vague docs:
        # https://docs.atlassian.com/aui/5.9.20/docs/lozenges.html
        if attr == "severity" and colour == "red":
            attr_dict["value"]["style"] = "lozenge-error"
        elif attr == "severity" and colour =="yellow":
            attr_dict["value"]["style"] = "lozenge-current"
        elif attr == "severity":
            attr_dict["value"]["style"] = "lozenge-complete"

        card["attributes"].append(attr_dict)

    try:
        logger.debug("Posting message to room %s" % room_id)
        nr_room.notification(hipchat_message,  color=colour,
                             notify=True, format="html", card=card)
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        response_error = json.loads(e.message)
        err_msg = "Error occured while talking to Hipchat: " + \
            response_error["error"]["message"]
        return error_response(err_msg, response)

    logger.info("Message sent to hipchat successfully")
    return response


def error_response(message, response, code=500):
    logger.error(message)
    response['statusCode'] = code
    response['body'] = message
    return json.dumps(response)


# __main__ will never be called by Lambda, I use this for CLI testing.
if __name__ == "__main__":

    # These here because I lazily copied the payload out of the AWS logs.
    null = None
    false = False
    true = True

    payloads = []

    # Full payload
    payloads.append({
            "body": "{\"owner\":\"\",\"severity\":\"INFO\",\"policy_url\":\"https://alerts.newrelic.com/accounts/0000000/policies/99999\",\"current_state\":\"open\",\"policy_name\":\"Robin Kearney's policy\",\"incident_url\":\"https://alerts.newrelic.com/accounts/0000000/incidents/6403470\",\"incident_acknowledge_url\":\"https://alerts.newrelic.com/accounts/0000000/incidents/6403470/acknowledge\",\"targets\":[{\"id\":\"3629392770913172224\",\"name\":\"3629392770913172224\",\"link\":\"https://infrastructure.newrelic.com/accounts/0000000/alertLanding?violationId=jklfelsdjkljfkldsjfkljkl\",\"labels\":{},\"product\":\"INFRASTRUCTURE\",\"type\":\"Host\"}],\"condition_id\":9999999,\"account_id\":1000000,\"event_type\":\"INCIDENT\",\"incident_id\":99999,\"runbook_url\":null,\"account_name\":\"RK-TEST-ACCOUNT\",\"details\":\"All CPU: Critical on git-192-168-70-171\",\"condition_name\":\"All CPU\",\"timestamp\":1495832844317, \"hipchat_room\": \"RKTest\"}",
        "resource": "/newrelic-hipchat-lambda",
        "requestContext": {
            "resourceId": "a99a99",
            "apiId": "redacted",
            "resourcePath": "/newrelic-hipchat-lambda",
            "httpMethod": "POST",
            "requestId": "test-invoke-request",
            "path": "/newrelic-hipchat-lambda",
            "accountId": "99999999999",
            "identity": {
                "apiKey": "test-invoke-api-key",
                "userArn": "arn:aws:iam::99999999999:root",
                "cognitoAuthenticationType": null,
                "accessKey": "REDACTED",
                "caller": "99999999999",
                "userAgent": "Apache-HttpClient/4.5.x (Java/1.8.0_112)",
                "user": "99999999999",
                "cognitoIdentityPoolId": null,
                "cognitoIdentityId": null,
                "cognitoAuthenticationProvider": null,
                "sourceIp": "test-invoke-source-ip",
                "accountId": "99999999999"
            },
            "stage": "test-invoke-stage"
        },
        "queryStringParameters": null,
        "httpMethod": "POST",
        "pathParameters": null,
        "headers": null,
        "stageVariables": null,
        "path": "/newrelic-hipchat-lambda",
        "isBase64Encoded": false
    })

    # new format condition_name - warning
    payloads.append({
            "body": "{\"owner\":\"\",\"severity\":\"INFO\",\"policy_url\":\"https://alerts.newrelic.com/accounts/0000000/policies/99999\",\"current_state\":\"open\",\"policy_name\":\"hb-infra-default-system-prod\",\"incident_url\":\"https://alerts.newrelic.com/accounts/0000000/incidents/6403470\",\"incident_acknowledge_url\":\"https://alerts.newrelic.com/accounts/0000000/incidents/6403470/acknowledge\",\"targets\":[{\"id\":\"3629392770913172224\",\"name\":\"3629392770913172224\",\"link\":\"https://infrastructure.newrelic.com/accounts/0000000/alertLanding?violationId=jklfelsdjkljfkldsjfkljkl\",\"labels\":{},\"product\":\"INFRASTRUCTURE\",\"type\":\"Host\"}],\"condition_id\":9999999,\"account_id\":1000000,\"event_type\":\"INCIDENT\",\"incident_id\":99999,\"runbook_url\":null,\"account_name\":\"RK-TEST-ACCOUNT\",\"details\":\"All CPU: Critical on git-192-168-70-171\",\"condition_name\":\"system-memory-used-percent-warn\",\"timestamp\":1495832844317, \"hipchat_room\": \"RKTest\"}",
        "resource": "/newrelic-hipchat-lambda",
        "requestContext": {
            "resourceId": "a99a99",
            "apiId": "redacted",
            "resourcePath": "/newrelic-hipchat-lambda",
            "httpMethod": "POST",
            "requestId": "test-invoke-request",
            "path": "/newrelic-hipchat-lambda",
            "accountId": "99999999999",
            "identity": {
                "apiKey": "test-invoke-api-key",
                "userArn": "arn:aws:iam::99999999999:root",
                "cognitoAuthenticationType": null,
                "accessKey": "REDACTED",
                "caller": "99999999999",
                "userAgent": "Apache-HttpClient/4.5.x (Java/1.8.0_112)",
                "user": "99999999999",
                "cognitoIdentityPoolId": null,
                "cognitoIdentityId": null,
                "cognitoAuthenticationProvider": null,
                "sourceIp": "test-invoke-source-ip",
                "accountId": "99999999999"
            },
            "stage": "test-invoke-stage"
        },
        "queryStringParameters": null,
        "httpMethod": "POST",
        "pathParameters": null,
        "headers": null,
        "stageVariables": null,
        "path": "/newrelic-hipchat-lambda",
        "isBase64Encoded": false
    })

    # new format condition_name - error
    payloads.append({
            "body": "{\"owner\":\"\",\"severity\":\"INFO\",\"policy_url\":\"https://alerts.newrelic.com/accounts/0000000/policies/99999\",\"current_state\":\"open\",\"policy_name\":\"hb-infra-default-system-prod\",\"incident_url\":\"https://alerts.newrelic.com/accounts/0000000/incidents/6403470\",\"incident_acknowledge_url\":\"https://alerts.newrelic.com/accounts/0000000/incidents/6403470/acknowledge\",\"targets\":[{\"id\":\"3629392770913172224\",\"name\":\"3629392770913172224\",\"link\":\"https://infrastructure.newrelic.com/accounts/0000000/alertLanding?violationId=jklfelsdjkljfkldsjfkljkl\",\"labels\":{},\"product\":\"INFRASTRUCTURE\",\"type\":\"Host\"}],\"condition_id\":9999999,\"account_id\":1000000,\"event_type\":\"INCIDENT\",\"incident_id\":99999,\"runbook_url\":null,\"account_name\":\"RK-TEST-ACCOUNT\",\"details\":\"All CPU: Critical on git-192-168-70-171\",\"condition_name\":\"system-memory-used-percent-error\",\"timestamp\":1495832844317, \"hipchat_room\": \"RKTest\"}",
        "resource": "/newrelic-hipchat-lambda",
        "requestContext": {
            "resourceId": "a99a99",
            "apiId": "redacted",
            "resourcePath": "/newrelic-hipchat-lambda",
            "httpMethod": "POST",
            "requestId": "test-invoke-request",
            "path": "/newrelic-hipchat-lambda",
            "accountId": "99999999999",
            "identity": {
                "apiKey": "test-invoke-api-key",
                "userArn": "arn:aws:iam::99999999999:root",
                "cognitoAuthenticationType": null,
                "accessKey": "REDACTED",
                "caller": "99999999999",
                "userAgent": "Apache-HttpClient/4.5.x (Java/1.8.0_112)",
                "user": "99999999999",
                "cognitoIdentityPoolId": null,
                "cognitoIdentityId": null,
                "cognitoAuthenticationProvider": null,
                "sourceIp": "test-invoke-source-ip",
                "accountId": "99999999999"
            },
            "stage": "test-invoke-stage"
        },
        "queryStringParameters": null,
        "httpMethod": "POST",
        "pathParameters": null,
        "headers": null,
        "stageVariables": null,
        "path": "/newrelic-hipchat-lambda",
        "isBase64Encoded": false
    })


    for test in payloads:
        print lambda_handler(test)
