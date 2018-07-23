Configuration
=============

The configuration takes place via 2 environment variables that should be set. These are:

  # REDIS_LOG_URI, contains an url to the redis, following the documentation from iana in the form of redis://[:password]@host:post/database
  # REDIS_LOG_CHANNEL, the channel used for logging, this should be the same as in the logstash configuration