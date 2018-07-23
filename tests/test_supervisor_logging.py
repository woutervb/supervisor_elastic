import os
import re
import socket
try:
    import socketserver
except ImportError:
    import SocketServer as socketserver
import subprocess
import threading

from time import sleep

from unittest import TestCase



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

                self.assertEqual(messages,
                    [
                        u'*3\r\n$7\r\nPUBLISH\r\n$6\r\npython\r\n$45\r\n'
                        u'<LogRecord: messages, 20, None, 0, "Test {i}\n">'.
                        format(pid=pid, i=i) for i in range(4)
                    ])
            finally:
                supervisor.terminate()

        finally:
            redis_srv.shutdown()
