import os
import re
import subprocess
import threading
from time import sleep
from unittest import TestCase

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver


def strip_volatile(message):
    """
    Strip volatile parts (PID, datetime) from a logging message.
    """

    volatile = (
        ('^\*\d\\\r\\\n\$\d\\\r\\\n\PUBLISH\\\r\\\n\$\d\\\r\\\npython\\\r'
         '\\\n\$\d+\\\r\\\n', ''),
        (r'"thread": \d+', '"thread": 0'),
        (r'"created": \d+\.\d+', '"created": "now"'),
        (r'"relativeCreated": \d+\.\d+', '"relativeCreated": "now"'),
        (r'"msecs": \d+\.\d+', '"msecs": "now"'),
        (r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z', 'DATE'),
    )

    for regexp, replacement in volatile:
        message = re.sub(regexp, replacement, message)

    return message


class SupervisorLoggingTestCase(TestCase):
    """
    Test logging.
    """

    maxDiff = None

    def test_logging(self):
        """
        Test logging.
        """

        messages = []

        class RedisHandler(socketserver.BaseRequestHandler):
            """
            Save received messages.
            """

            def handle(self):
                messages.append(self.request.recv(4096).strip().decode())

        redis_srv = socketserver.TCPServer(('127.0.0.1', 0), RedisHandler)
        try:
            threading.Thread(target=redis_srv.serve_forever).start()

            env = os.environ.copy()
            env['REDIS_LOG_URI'] = 'redis://%s:%s' % \
                                   (redis_srv.server_address[0],
                                    redis_srv.server_address[1])
            print(env['REDIS_LOG_URI'])
            env['REDIS_LOG_CHANNEL'] = 'python'

            mydir = os.path.dirname(__file__)

            supervisor = subprocess.Popen(
                ['supervisord', '-c',
                 os.path.join(mydir, 'supervisord.conf')],
                env=env,
            )
            try:

                sleep(3)

                pid = subprocess.check_output(
                    ['supervisorctl', 'pid', 'messages']).decode().strip()

                sleep(8)

                self.assertEqual(
                    list(map(strip_volatile, messages)), [
                        u'{"relativeCreated": "now", '
                        u'"process": %s, "@timestamp": "DATE", '
                        u'"module": "supervisor_elastic", '
                        u'"funcName": null, "message": "Test %s\\n", '
                        u'"name": "messages", "thread": 0, '
                        u'"created": "now", "threadName": "MainThread", '
                        u'"msecs": "now", "filename": null, "levelno": 20, '
                        u'"processName": "MainProcess", "source_host": "", '
                        u'"pathname": null, "lineno": 0, "@version": 1, '
                        u'"levelname": "INFO"}' % (pid, i // 2)
                        for i in range(8)
                    ])
            finally:
                supervisor.terminate()

        finally:
            redis_srv.shutdown()
