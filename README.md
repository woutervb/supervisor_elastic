Status
======
[![Build Status](https://travis-ci.org/woutervb/supervisor_elastic.png)](https://travis-ci.org/woutervb/supervisor_elastic)

Introduction
============

Connecting the logging from python to elasticsearch is not always trivial, as there are multiple routes that can be taken.
This project uses, redis as a middleman. The main reason is, that redis is relative simple to setup in an high-availability
setup, so that it will not (or hardly) block the main processing loop in python.
The time to process the data is completely dependend on the performance of the logstash agent, that will read log records
from redis and put them in elasticsearch for future processing.
This setup has proven to be quite stable for already a few year. But one of the things missing, was the ability to add
logging from supervisor to this log system. Obviously it would be possible to use filebeat to read log file(s) and then
send them to logstash, but as supervisor is written in python, it makes more sense to use the same route via redis.
This is wat this project has created.

Configuration
=============

The configuration should take place at 2 locations, that is in supervisor, and in logstash. The supervisor configuration
is needed to send the messages to redis, and the logstash configuration is neede to pull the data from redis.

Configuration of supervisor
---------------------------

In supervisor we use 2 environment variables to configure the software that send the data to elasticsearch. These
variables are listed below.

  * REDIS_LOG_URI, contains an url to the redis, following the documentation from iana in the form of redis://[:password]@host:post/database
  * REDIS_LOG_CHANNEL, the channel used for logging, this should be the same as in the logstash configuration

so an example section of the supervisor.conf would be:

    [eventlistener:logging]
    command = supervisor_elastic
    events = PROCESS_LOG
    environment = REDIS_LOG_URI="redis://dockerhost",REDIS_LOG_CHANNEL="app:python"

Another importand thing to notice, is that in each program definition inside the supervisor configuration the following
key's should be activated:

    stdout_events_enabled=true
    stderr_events_enabled=true

These key's will ensure that any data that is send to log file(s) is also send to the eventlistner(s) that are defined.

Configuration of logstash
-------------------------

And the equivalent section in logstash would be:

    # Collect python logging from redis
    input {
      redis {
        host => "dockerhost"
        codec => json
        data_type => "channel"
        type => "python"
        key  => "app:python"
        tags => ["json"]
      }
    }

Things that should be equal, is at least the key (in logstash) that should be equal to REDIS_LOG_CHANNEL in the supervisor
configuration.

Notice
======

Parts of this project are inspired from: https://github.com/infoxchange/supervisor-logging, so they should be mentioned.
