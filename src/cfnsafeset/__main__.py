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
import cfnsafeset.core

LOGGER = logging.getLogger('cfnsafeset')
CONFIG_FILE = '/data/stateful-resources.yaml'


def main():
    """Main function"""
    args = cfnsafeset.core.get_args()
    config = cfnsafeset.core.init_config(CONFIG_FILE)
    monitored_change_types = config['ChangeTypes']
    LOGGER.debug('Monitored change types from config: %s',
                 monitored_change_types)
    stateful_resources = set(config['StatefulResources'])
    LOGGER.debug('Stateful resources from config: %s', stateful_resources)
    if args.list:
        cfnsafeset.core.show_stateful_resources(stateful_resources)
        return 0
    if args.file:
        changes = cfnsafeset.core.load_cs_file(args.file)
    else:
        changes = cfnsafeset.core.get_change_set(
            args.changeset, args.stack, args.region)
    if cfnsafeset.core.detect_stateful_replace(changes, monitored_change_types, stateful_resources):
        return 2
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, TypeError):
        LOGGER.error(ValueError)
