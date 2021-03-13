#!/bin/bash

tail -n 10 /home/ubuntu/tweepy-twitter-bot1/scripts/cron-job.log > /home/ubuntu/tweepy-twitter-bot1/scripts/cron-job.log.tmp
mv -f /home/ubuntu/tweepy-twitter-bot1/scripts/cron-job.log.tmp /home/ubuntu/tweepy-twitter-bot1/scripts/cron-job.log
