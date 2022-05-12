# Stop AWS EC2 Instances with missing or empty name & environment tags - Serverless
Check if AWS EC2 instances that are running have valid "Name" and "Environment" tags, if not then notify the creator and stop the instance after 6 hours.

Using: EventBridge(Cloudwatch), Lambda, Step Functions, AWS SDK for Python (BOTO3)


## Task
- Create an AWS Lambda function which would run every hour and check EC2 instances which don’t have ‘Environment’ and ‘Name’ tags attached on it.
- It should check the ‘created by’ tag whose value would be an emailId and if it finds an instance which doesn't have the aforementioned tags, it should send them an email to remind them to tag the instance.
- The email should contain the instance ID and the tag keys it is missing.
- Once 6 hours have passed after sending the email, it should terminate the instance with an email notifying the user of the same.

## Assumptions
- Every EC2 instance can have any number of tags, assume that ‘created by’ tag would always be present and your code should ensure that ‘Environment’ and ‘Name’ tags are present.
- Instances having "Environment" and "Name" Tags as keys, but with empty values associated need to be stopped too.
- Although tags in AWS are case sensitve, While checking for the tags comparison should be case **insensitive**.
- First verified email address in the AWS account should be used as a Source to send emails.


## Solution

![Flow](https://user-images.githubusercontent.com/19901671/168099706-cb01a58d-67e2-471e-a1b2-10b9a528ef23.png)


1) An EventBridge rule triggers the Lambda function (checkEC2InstancesForTagCompliance) every hour
2) Lambda Function (checkEC2InstancesForTagCompliance) reads tags of all running EC2 instances. For instances with missing or empty "Name" and "Environment" tag, it outputs a list of their ids and sends a notification over email to the creator of the instance. It also triggers an execution of a State Machine - AWS Step Function(stopInstancesStateMachine)
3) State: Wait for 6 hours. Then Lambda function (stopNonCompliantEC2Instances) is invoked.
4) Lambda function (stopNonCompliantEC2Instances) checks the parsed non-compliant instances again, and in case they are still non-compliant then stops them and notifies the creator of the stoppage over email.


## How to set up and deploy

1) Set Up Email or Domain for AWS SES

2) Create IAM Policies & Roles for each of the following using the JSON file from the IAM directory
    - Lambda Function (checkEC2InstancesForTagCompliance)
    - Lambda Function (stopNonCompliantEC2Instances)
    - State Machine (stopInstancesStateMachine)

3) Create Two Lambda Functions using the files in the LambdaFunctions directory
    - *For both functions, Set timeout to 6 seconds*
    - *For stopNonCompliantEC2Instances function, Change the hard-coded ARN for state machine on line 62 with the ARN for your state machine*
        
4) Create AWS Step Function - State Machine using the JSON file in the StateMachine directory
    - *Change ARN for lambda function in the JSON file with the ARN for your function*

5) Test the Lambda Functions

6) Create Event Bridge Rule - Every 1 hour, Trigger the Lambda function (checkEC2InstancesForTagCompliance)

