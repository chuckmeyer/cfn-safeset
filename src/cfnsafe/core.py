"""
  Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.

  Permission is hereby granted, free of charge, to any person obtaining a copy of this
  software and associated documentation files (the "Software"), to deal in the Software
  without restriction, including without limitation the rights to use, copy, modify,
  merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
  PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from __future__ import print_function
import logging
import argparse
import sys
import os
import pkg_resources
from boto3 import client
from botocore.exceptions import ClientError
import yaml

LOGGER = logging.getLogger('cfnsafe')


def init_logger(use_debug):
    """ Set log level and format """
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        #    '%(asctime)s %(levelname)-8s %(message)s')
        '%(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    if use_debug:
        LOGGER.setLevel(logging.DEBUG)


def init_config(config_file):
    """ Load resource data """
    LOGGER.debug('Loading config from file: %s', config_file)
    filename = pkg_resources.resource_filename(
        __name__,
        config_file
    )

    with open(filename) as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg


def create_parser():
    """ Set up command line arguements """
    parser = argparse.ArgumentParser(
        description='CloudFormation ChangSet Arbiter')

    standard = parser.add_argument_group('Standard')
    advanced = parser.add_argument_group('Advanced / Debugging')

    standard.add_argument(
        '-c', '--changeset', metavar='CHANGESET',
        help='The CloudFormation change set to be evaluated')
    standard.add_argument(
        '-s', '--stack', metavar='STACKNAME',
        help='The stack name associated with this change set')
    standard.add_argument(
        '-r', '--region', metavar='REGION', default='us-east-1',
        help='The region where this change set exists')
    advanced.add_argument(
        '-d', '--debug', help='Enable debug logging', action='store_true')
    advanced.add_argument(
        '-l', '--list', help='List stateful resources', action='store_true'
    )
    return parser


def get_args():
    """ Do first round of parsing parameters to set options """
    parser = create_parser()
    args = parser.parse_args()
    if args.list:
        return args
    if not args.changeset:
        LOGGER.error('%s: You must specify a valid change set and stack name (-c/-s)',
                     os.path.basename(sys.argv[0]))
        sys.exit(1)
    if not args.stack:
        LOGGER.error('%s: You must specify a valid change set and stack name (-c/-s)',
                     os.path.basename(sys.argv[0]))
        sys.exit(1)
    return args


def get_change_set(change_set, stack, region):
    """ Retrieve ChangeSet data via API """
    LOGGER.debug('Retrieving change set %s for stack %s in region %s',
                 change_set, stack, region)
    try:
        cf_client = client('cloudformation', region_name=region)
        response = cf_client.describe_change_set(
            ChangeSetName=change_set,
            StackName=stack
        )
        LOGGER.debug(response['Changes'])
        return response['Changes']

    except cf_client.exceptions.ChangeSetNotFoundException:
        LOGGER.error('Change set %s not found for stack %s in region %s',
                     change_set, stack, region)
        sys.exit(1)
    except ClientError as err:
        if err.response['Error']['Code'] == 'ValidationError':
            LOGGER.error('Cannot retrieve stack %s in region %s',
                         stack, region)
        else:
            LOGGER.error('Unexpected error: %s', err)
        sys.exit(1)


def show_stateful_resources(stateful_resources):
    """ List stateful resources defined in resource data """
    print('List of stateful resources:')
    for resource in stateful_resources:
        print(' * %s' % resource)


def is_stateful_replace(change, stateful_resources):
    """ Boolean check if current change references a stateful resource """
    return change['Replacement'] == 'True' and change['ResourceType'] in stateful_resources


def stateful_replace_properties(change):
    """ List of property changes that triggered replace action """
    property_list = set()
    for detail in change['Details']:
        if detail['Target']['Attribute'] == 'Properties':
            if detail['Target']['RequiresRecreation'] != 'Never':
                property_list.add(detail['Target']['Name'])
    return property_list
