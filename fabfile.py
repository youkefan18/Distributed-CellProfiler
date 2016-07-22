import boto
import boto.s3
import json
import os
import time

from boto.exception import BotoServerError
from cStringIO import StringIO
from ConfigParser import ConfigParser
from fabric.api import local, quiet, env, run, put, cd
from urllib2 import unquote
from zipfile import ZipFile, ZIP_DEFLATED

# Constants (User configurable), imported from config.py

from config import *

# Constants (Application specific)
SSH_KEY_DIR = os.environ['HOME'] + '/.ssh'
ECS_TASK_NAME = APP_NAME + 'Task'
ECS_SERVICE_NAME = APP_NAME + 'Service'

# Constants (OS specific)
USER = os.environ['HOME'].split('/')[-1]
AWS_CONFIG_FILE_NAME = os.environ['HOME'] + '/.aws/config'
AWS_CREDENTIAL_FILE_NAME = os.environ['HOME'] + '/.aws/credentials'

# Constants
AWS_CLI_STANDARD_OPTIONS = (
    '    --region ' + AWS_REGION +
    '    --profile ' + AWS_PROFILE +
    '    --output json'
)

SSH_USER = 'ec2-user'
WAIT_TIME = 5  # seconds to allow for eventual consistency to kick in.
RETRIES = 5  # Number of retries before we give up on something.

# Templates and embedded scripts

TASK_DEFINITION = {
    "family": APP_NAME,
    "containerDefinitions": [
        {
            "environment": [
                {
                    "name": "AWS_REGION",
                    "value": AWS_REGION
                }
	    ],
            "name": APP_NAME,
            "image": DOCKERHUB_TAG,
            "cpu": CPU_SHARES,
            "memory": MEMORY,
            "essential": True,
	    "privileged": True
        }
    ]
}

# Functions


# Dependencies and credentials.


def update_dependencies():
    local('pip2 install -r files/requirements.txt')


def get_aws_credentials():
    config = ConfigParser()
    config.read(AWS_CONFIG_FILE_NAME)
    config.read(AWS_CREDENTIAL_FILE_NAME)
    return config.get(AWS_PROFILE, 'aws_access_key_id'), config.get(AWS_PROFILE, 'aws_secret_access_key')


# Amazon S3

def show_bucket_name():
    print("Your bucket name is: " + AWS_BUCKET)

# Amazon ECS

def generate_dockerfile():
	return DOCKERFILE 


def show_dockerfile():
    print generate_dockerfile()


def generate_task_definition():
    task_definition = TASK_DEFINITION.copy()
    key, secret = get_aws_credentials()
    task_definition['containerDefinitions'][0]['environment'] += [
        {
            'name': 'SQS_QUEUE_URL',
            'value': get_queue_url()
        },
	{
	    "name": "AWS_ACCESS_KEY_ID",
	    "value": key
	},
	{
	    "name": "AWS_SECRET_ACCESS_KEY",
	    "value": secret
	},
	{
	    "name": "AWS_BUCKET",
	    "value": AWS_BUCKET
	},
	{
	    "name": "DOCKER_CORES",
	    "value": str(DOCKER_CORES)
	},
	{
	    "name": "SECONDS_TO_START",
	    "value": str(SECONDS_TO_START)
	}
    ]
    return task_definition


def show_task_definition():
    print json.dumps(generate_task_definition(), indent=4)


def update_ecs_task_definition():
    task_definition_string = json.dumps(generate_task_definition())

    response = local(
        'aws ecs register-task-definition' +
        '    --family ' + ECS_TASK_NAME +
        '    --cli-input-json \'' + task_definition_string + '\'' +
        AWS_CLI_STANDARD_OPTIONS,
        capture=True
    )
    print response

def create_or_update_ecs_service():
    # Create the service with no workers (0 desired count)
    info = local('aws ecs list-services', capture=True)
    data = json.loads(info)
    service = [srv for srv in data['serviceArns'] if srv.endswith(ECS_SERVICE_NAME)]
    if len(service) >= 0:
        print 'Service exists. Removing'
	local('aws ecs delete-service --cluster ' + ECS_CLUSTER + 
		  ' --service ' + ECS_SERVICE_NAME,
		  capture=True)
	time.sleep(WAIT_TIME)

    print 'Creating new service'
    local('aws ecs create-service --cluster ' + ECS_CLUSTER + 
	      ' --service-name ' + ECS_SERVICE_NAME + 
	      ' --task-definition ' + ECS_TASK_NAME + 
	      ' --desired-count 0 ',
	      capture=True
    )


# Amazon SQS


def get_queue_url():
    result = local(
        'aws sqs list-queues' +
        AWS_CLI_STANDARD_OPTIONS,
        capture=True
    )

    if result is not None and result != '':
        result_struct = json.loads(result)
        if isinstance(result_struct, dict) and 'QueueUrls' in result_struct:
            for u in result_struct['QueueUrls']:
                if u.split('/')[-1] == SQS_QUEUE_NAME:
                    return u

    return None


def get_or_create_queue():
    u = get_queue_url()
    if u is None:
        local(
            'aws sqs create-queue' +
            '    --queue-name ' + SQS_QUEUE_NAME + 
	    '    --attributes VisibilityTimeout=' + str(SQS_MESSAGE_VISIBILITY) +
            AWS_CLI_STANDARD_OPTIONS,
            capture=True
        )

        tries = 0
        while True:
            time.sleep(WAIT_TIME)
            u = get_queue_url()

            if u is not None and tries < RETRIES:
                return u

            tries += 1


# High level functions. Call these as "fab <function>"


def update_bucket():
    get_or_create_bucket()


def update_ecs():
    update_ecs_task_definition()
    create_or_update_ecs_service()


def update_queue():
    get_or_create_queue()


def setup():
    update_dependencies()
    update_queue()
    update_ecs()
    show_bucket_name()
