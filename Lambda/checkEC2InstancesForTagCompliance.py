# This file has a hardcoded ARN for a State Machine (AWS Step Function) on line 64, replace it with ARN for your state machine
import boto3
import json
import datetime


def getTagValues(instance):

    hasNameTag = False
    hasEnvTag = False
    email = ""

    for tag in instance.tags:
        if tag["Key"].lower() == "name" and tag["Value"] != "":
            hasNameTag = True
        if tag["Key"].lower() == "environment" and tag["Value"] != "":
            hasEnvTag = True
        if tag["Key"] == "created by":
            email = tag["Value"]
        if hasNameTag and hasEnvTag and email != "":
            break

    return {"hasName": hasNameTag, "hasEnvironment": hasEnvTag, "creatorEmailID": email}


def sendEmailReminder(id, tags):

    ses = boto3.client("ses")

    if tags["hasName"] == False and tags["hasEnvironment"] == False:
        missingTagMessage = "Name and Environment tags"
    elif tags["hasName"] == False:
        missingTagMessage = "Name tag"
    elif tags["hasEnvironment"] == False:
        missingTagMessage = "Environment tag"

    body = f"EC2 instance with id {id} will be stopped after 6 hours from now because it does not have a valid {missingTagMessage}. Please fix it before then to avoid the instance being stopped."

    response = ses.send_email(
        Source=ses.list_verified_email_addresses()["VerifiedEmailAddresses"][0],
        Destination={"ToAddresses": [tags["creatorEmailID"]]},
        Message={
            "Subject": {
                "Data": "EC2 Instance - Will be Stopped in 6 hrs - Tag Non Compliance",
                "Charset": "UTF-8",
            },
            "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
        },
    )

    # print(response)
    return response["MessageId"]


def lambda_handler(event, context):

    ec2 = boto3.resource("ec2")
    instances = ec2.instances.filter(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    sfn_client = boto3.client("stepfunctions")
    state_machine_arn = (
        "arn:aws:states:us-east-1:076496163195:stateMachine:MyStateMachine"
    )

    nonCompliantInstancesIDs = []
    emailMessageIDs = []
    response = {}

    for instance in instances:

        tags = getTagValues(instance)

        if tags["hasName"] and tags["hasEnvironment"]:
            continue

        else:
            nonCompliantInstancesIDs.append(instance.id)
            emailMessageIDs.append(sendEmailReminder(instance.id, tags))

    response["statusCode"] = 200
    response["nonCompliantInstancesIDs"] = nonCompliantInstancesIDs
    response["emailMessageIDs"] = emailMessageIDs

    # AWS Step Function Execution
    if nonCompliantInstancesIDs:
        stepfunction_response = sfn_client.start_execution(
            stateMachineArn=state_machine_arn,
            name=f"RanAt{int(datetime.datetime.now().timestamp())}",
            input=json.dumps(response),
        )
        print(stepfunction_response)

    return response
