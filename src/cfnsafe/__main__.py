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
import logging
import sys
import cfnsafe.core

LOGGER = logging.getLogger('cfnsafe')
CONFIG_FILE = '/data/stateful-resources.yaml'


def main():
  stateful_replace = False
  args = cfnsafe.core.get_args()
  cfnsafe.core.init_logger(args.debug)
  config = cfnsafe.core.init_config(CONFIG_FILE)
  monitored_change_types = config['ChangeTypes']
  LOGGER.debug('Monitored change types from config: %s' %
               monitored_change_types)
  stateful_resources = set(config['StatefulResources'])
  LOGGER.debug('Stateful resources from config: %s' % stateful_resources)
  if args.list:
    cfnsafe.core.show_stateful_resources(stateful_resources)
    return(0)
  changes = cfnsafe.core.get_change_set(args.changeset, args.stack, args.region)
  for change in changes:
    if change['Type'] in monitored_change_types:
      LOGGER.debug('Monitored resource type: %s' % change['Type'])
      if cfnsafe.core.is_stateful_replace(change[monitored_change_types[change['Type']]], stateful_resources):
        properties = cfnsafe.core.list_stateful_replace_properties(
            change[monitored_change_types[change['Type']]])
        LOGGER.warning('Replace required for stateful resource %s (%s) due to changes to these properties: %s' %
                       (change['ResourceChange']['LogicalResourceId'], change['ResourceChange']['ResourceType'], list(properties)))
        stateful_replace = True
      else:
        LOGGER.info('Non-stateful resource skipped: %s (%s)' %
                    (change['ResourceChange']['LogicalResourceId'], change['ResourceChange']['ResourceType']))
  if stateful_replace:
    return(2)
  else:
    return(0)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, TypeError):
        LOGGER.error(ValueError)
