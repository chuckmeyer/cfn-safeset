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
import cfnsafeset.core  # pylint: disable=E0401
from testlib.testcase import BaseTestCase

LOGGER = logging.getLogger('cfnsafeset')


class TestLogging(BaseTestCase):
    """Test Logging Arguments """
    def tearDown(self):
        """Setup"""
        for handler in LOGGER.handlers:
            LOGGER.removeHandler(handler)

    def test_logging_info(self):
        """Test success run"""

        cfnsafeset.core.configure_logging(False)
        self.assertEqual(logging.INFO, LOGGER.level)
        self.assertEqual(len(LOGGER.handlers), 1)

    def test_logging_debug(self):
        """Test debug level"""

        cfnsafeset.core.configure_logging(True)
        self.assertEqual(logging.DEBUG, LOGGER.level)
        self.assertEqual(len(LOGGER.handlers), 1)
