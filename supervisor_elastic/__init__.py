import os
import sys
import redis
import logging
import json
import socket
import datetime
import traceback as tb


def _default_json_default(obj):
    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    else:
        return str(obj)


class RedisFormatter(logging.Formatter):
    def __init__(self,
                 fmt=None,
                 datafmt=None,
                 style='%',
                 json_cls=None,
                 json_default=_default_json_default):
        if fmt is not None:
            self._fmt = json.loads(fmt)
        else:
            self._fmt = {}
        self.json_default = json_default
        self.json_cls = json_cls
        if 'extra' not in self._fmt:
            self.defaults = {}
        else:
            self.defaults = self._fmt['extra']
        if 'source_host' in self._fmt:
            self.source_host = self._fmt['source_host']
        else:
            try:
                self.source_host = socket.gethostbyname()
            except Exception:
                self.source_host = ''

    def format(self, record):
        fields = record.__dict__.copy()

        if isinstance(record.msg, dict):
            fields.update(record.msg)
            fields.pop('msg')
            msg = ''
        else:
            msg = record.getMessage()

        if 'msg' in fields:
            fields.pop('msg')

        if 'message' in fields:
            fields.pop('message')

        if 'args' in fields:
            fields.pop('args')

        if 'exc_info' in fields:
            if fields['exc_info']:
                formatted = tb.format_exception(*fields['exc_info'])
                fields['exception'] = formatted
            fields.pop('exc_info')

        if 'exc_text' in fields and not fields['exc_text']:
            fields.pop('exc_text')

        now = datetime.datetime.utcnow()
        base_log = {
            '@timestamp':
            now.strftime('%Y-%m-%dT%H:%M:%S') +
            '.%03d' % (now.microsecond / 1000) + 'Z',
            '@version':
            1,
            'source_host':
            self.source_host,
            'message':
            msg
        }
        base_log.update(fields)

        logr = self.defaults.copy()
        logr.update(base_log)

        json_dict = json.dumps(
            logr, default=self.json_default, cls=self.json_cls)
        return json_dict


class RedisHandler(logging.Handler):
    def __init__(self, redis_uri, redis_channel, formatter, level):
        logging.Handler.__init__(self, level)
        self.redis_client = redis.Redis.from_url(redis_uri)
        self.channel = redis_channel
        self.formatter = formatter

    def emit(self, record):
        try:
            self.redis_client.publish(self.channel, self.format(record))
        except redis.RedisError:
            pass


def get_headers(line):
    return dict([x.split(':') for x in line.split()])


def eventdata(payload):
    headerinfo, data = payload.split('\n', 1)
    headers = get_headers(headerinfo)

    return headers, data


def supervisor_events(stdin, stdout):
    while True:
        stdout.write('READY\n')
        stdout.flush()

        line = stdin.readline()
        headers = get_headers(line)

        payload = stdin.read(int(headers['len']))
        event_headers, event_data = eventdata(payload)

        yield event_headers, event_data

        stdout.write('RESULT 2\nOK')
        stdout.flush()


def main():
    """Main application loop"""

    env = os.environ

    try:
        redis_uri = env['REDIS_LOG_URI']
        redis_channel = env['REDIS_LOG_CHANNEL']
    except KeyError:
        sys.exit('REDIS_LOG_URI and REDIS_LOG_CHANNEL are required')

    handler = RedisHandler(
        redis_uri=redis_uri,
        redis_channel=redis_channel,
        formatter=RedisFormatter(),
        level=logging.NOTSET,
    )

    for event_headers, event_data in supervisor_events(sys.stdin, sys.stdout):
        event = logging.LogRecord(
            name=event_headers['processname'],
            level=logging.INFO,
            pathname=None,
            lineno=0,
            msg=event_data,
            args=(),
            exc_info=None,
        )
        event.process = int(event_headers['pid'])
        event.module = 'supervisor_elastic'
        # event.__dict__.update(event_headers)
        handler.handle(event)


if __name__ == '__main__':

    main()
