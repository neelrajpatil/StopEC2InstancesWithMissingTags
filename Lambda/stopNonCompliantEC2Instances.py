import json
import boto3
from botocore.exceptions import ClientError
import json


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


def sendStoppedInstanceEmail(id, tags):

    ses = boto3.client("ses")

    if tags["hasName"] == False and tags["hasEnvironment"] == False:
        missingTagMessage = "Name and Environment tags"
    elif tags["hasName"] == False:
        missingTagMessage = "Name tag"
    elif tags["hasEnvironment"] == False:
        missingTagMessage = "Environment tag"

    body = f"EC2 instance with id {id} is stopped because it does not have a valid {missingTagMessage}. Please fix it."

    response = ses.send_email(
        Source=ses.list_verified_email_addresses()["VerifiedEmailAddresses"][0],
        Destination={"ToAddresses": [tags["creatorEmailID"]]},
        Message={
            "Subject": {
                "Data": "EC2 Instance Stopped - Tag Non Compliance",
                "Charset": "UTF-8",
            },
            "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
        },
    )
    return response["MessageId"]


def stop(instance):

    # Dry run - permissions
    try:
        instance.stop(DryRun=True)
    except ClientError as e:
        if "DryRunOperation" not in str(e):
            raise

    # Actual run
    try:
        response = instance.stop(DryRun=False)
        # print(response)
    except ClientError as e:
        print(e)


def lambda_handler(event, context):

    nonCompliantInstancesIDs = event["nonCompliantInstancesIDs"]
    stoppedInstancesIDs = []
    emailMessageIDs = []
    response = {}

    ec2 = boto3.resource("ec2")
    instances = ec2.instances.filter(
        InstanceIds=nonCompliantInstancesIDs,
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}],
    )

    for instance in instances:

        tags = getTagValues(instance)

        if tags["hasName"] and tags["hasEnvironment"]:
            continue

        else:
            stoppedInstancesIDs.append(instance.id)
            emailMessageIDs.append(sendStoppedInstanceEmail(instance.id, tags))
            stop(instance)

    response["statusCode"] = 200
    response["prevNonCompliantInstancesIDs"] = nonCompliantInstancesIDs
    response["stoppedInstancesIDs"] = stoppedInstancesIDs
    response["emailMessageIDs"] = emailMessageIDs
    return response
