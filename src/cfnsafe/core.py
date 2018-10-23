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
import json
import pkg_resources
from boto3 import client
from botocore.exceptions import ClientError
import yaml
from cfnsafe.version import __version__

LOGGER = logging.getLogger('cfnsafe')


def init_logger(use_debug):
    """ Set log level and format """
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    if use_debug:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.WARNING)

    formatter = logging.Formatter('%(levelname)-8s %(message)s')
        #    '%(asctime)s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    # make sure all other log handlers are removed before adding it back
    for handler in LOGGER.handlers:
        LOGGER.removeHandler(handler)
    LOGGER.addHandler(handler)


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
    """ Set up command line arguments """
    parser = argparse.ArgumentParser(
        description='CloudFormation ChangeSet safety check')

    standard = parser.add_argument_group('Standard')
    advanced = parser.add_argument_group('Advanced / Debugging')

    standard.add_argument(
        '-c', '--changeset', metavar='CHANGESET',
        help='The CloudFormation change set to be evaluated')
    standard.add_argument(
        '-s', '--stack', metavar='STACKNAME',
        help='The stack name associated with this change set')
    standard.add_argument(
        '-f', '--file', metavar='STACKNAME',
        help='File containing a valid CloudFormation change set')
    standard.add_argument(
        '-r', '--region', metavar='REGION', default='us-east-1',
        help='The region where this change set exists')
    standard.add_argument(
        '-v', '--version', help='Version of cfn-safe', action='version',
        version='%(prog)s {version}'.format(version=__version__))
    advanced.add_argument(
        '-d', '--debug', help='Enable debug logging', action='store_true')
    advanced.add_argument(
        '-l', '--list', help='List stateful resources', action='store_true')
    return parser


def get_args():
    """ Do first round of parsing parameters to set options """
    parser = create_parser()
    args = parser.parse_args()
    if args.list:
        return args

    init_logger(args.debug)

    if (not args.changeset and not args.stack) and not args.file:
        LOGGER.error('%s: You must specify a valid change set and stack name (-c/-s)'
                     'or file location (-f)',
                     os.path.basename(sys.argv[0]))
        sys.exit(1)
    return args


def get_change_set(change_set, stack, region):
    """ Retrieve change set data via API """
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


def load_cs_file(filename):
    """ Retrieve change set data from a file """
    try:
        with open(filename) as change_file:
            change_set = json.load(change_file)
        return change_set['Changes']
    except IOError as err:
        if err.errno == 2:
            LOGGER.error('Change set file not found: %s', filename)
        elif err.errno == 21:
            LOGGER.error(
                'Change set references a directory, not a file: %s', filename)
        elif err.errno == 13:
            LOGGER.error(
                'Permission denied when accessing change set file: %s', filename)
        sys.exit(1)
    except Exception as json_err: # pylint: disable=W0703
        LOGGER.error(
            'Tried to parse %s as JSON but got error: %s', filename, str(json_err))
        sys.exit(1)


def show_stateful_resources(stateful_resources):
    """ List stateful resources defined in resource data """
    print('List of stateful resources:')
    for resource in stateful_resources:
        print(' * %s' % resource)


def is_stateful(change, stateful_resources):
    """ Boolean check if current change references a stateful resource """
    return change['ResourceType'] in stateful_resources


def is_replace(change):
    """ Boolean check if current change references a stateful resource """
    return change['Replacement'] == 'True'


def detect_stateful_replace(changes, monitored_change_types, stateful_resources):
    """ Iterate through changes and look for stateful resources with replace actions """
    stateful_replace = False
    for change in changes:
        if change['Type'] in monitored_change_types:
            LOGGER.debug('Monitored resource type: %s', change['Type'])
            if is_stateful(
                    change[monitored_change_types[change['Type']]],
                    stateful_resources
            ):
                LOGGER.info('Stateful resource detected: %s (%s)',
                            change['ResourceChange']['LogicalResourceId'],
                            change['ResourceChange']['ResourceType'])
                if is_replace(
                        change[monitored_change_types[change['Type']]]):
                    properties = stateful_replace_properties(
                        change[monitored_change_types[change['Type']]])
                    LOGGER.warning(
                        'Replace required for stateful resource %s (%s)'
                        'due to changes to these properties: %s',
                        change['ResourceChange']['LogicalResourceId'],
                        change['ResourceChange']['ResourceType'],
                        list(properties))
                    stateful_replace = True
            else:
                LOGGER.info('Non-stateful resource skipped: %s (%s)',
                            change['ResourceChange']['LogicalResourceId'],
                            change['ResourceChange']['ResourceType'])
    return stateful_replace


def stateful_replace_properties(change):
    """ List of property changes that triggered replace action """
    property_list = set()
    for detail in change['Details']:
        if detail['Target']['Attribute'] == 'Properties':
            if detail['Target']['RequiresRecreation'] != 'Never':
                property_list.add(detail['Target']['Name'])
    return property_list
