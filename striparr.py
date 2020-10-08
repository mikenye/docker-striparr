#!/usr/bin/env python

__version__ = "2020-04-11"

import sys
import os
import datetime
import logging
# import time
import subprocess
import re
import shutil
# import json
# from pprint import pprint
from flask import Flask, request, abort
# from flask.logging import default_handler
from celery import Celery
from celery.utils.log import get_task_logger

# Set up Flask App & Celery config
app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.config['CELERY_broker_url'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'
app.config['worker_log_format'] = '[%(asctime)s] [%(levelname)s] %(message)s'


# Set up Flask app logging
class App_Logger:
    def info(self, message):
        self._log(message, 'INFO')
    def error(self, message):
        self._log(message, 'ERROR')
    def _log(self, message, levelname):
        logdata = dict()
        dtnow = datetime.datetime.now()
        logdata['asctime'] = dtnow.strftime('%Y-%m-%d %H:%M:%S,')
        logdata['asctime'] += dtnow.strftime('%f')[:3]
        logdata['levelname'] = levelname
        logdata['remote_addr'] = request.remote_addr
        logdata['user_agent'] = request.user_agent
        logdata['message'] = message
        print('[%(asctime)s: %(levelname)s] [%(remote_addr)s] [%(user_agent)s] %(message)s' % logdata)
        sys.stdout.flush()


app_logger = App_Logger()


# Set up Celery
celery = Celery(app.name, broker=app.config['CELERY_broker_url'])
celery.conf.update(app.config)
# Disable Celery logging twice
celery_logger = get_task_logger(__name__)
celery_logger.removeHandler(celery_logger.handlers[0])


# Worker task
@celery.task
def worker(filetostrip):

    # compile regex
    re_metadata_data = re.compile('^(?P<key>[^=]+)=(?P<value>.+)$')

    # define banned metadata keys
    # if a file contains metadata in these keys it'll be stripped of all metadata
    banned_metadata_keys = [
        'comment',
        'title',
        ]

    # perform ffmpeg metadata scan
    celery_logger.info('Checking: "%s"' % (filetostrip))
    metadata_scan = subprocess.run(
        ["ffmpeg",
         "-i",
         filetostrip,
         "-f",
         "ffmetadata",
         "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True)

    # make sure ffmpeg scan worked ok
    if metadata_scan.returncode != 0:
        celery_logger.error('ffmpeg metadata scan failed: "%s"' % (metadata_scan.stderr))

    else:

        # check output for metadata we want to remove
        found_banned_metadata_keys = False
        for metadata_line in metadata_scan.stdout.decode().split('\n'):
            m = re_metadata_data.match(metadata_line)
            if m:
                mgd = m.groupdict()
                if mgd['key'] in banned_metadata_keys:
                    found_banned_metadata_keys = True

        # if we found metadata we want to remove
        if found_banned_metadata_keys:

            filetostrip_name, filetostrip_ext = filetostrip.rsplit('.', 1)

            # Use temp file /tmp/whatever.ext
            stripped_filepath = os.path.join(
                os.path.abspath(os.sep),
                'tmp',
                os.path.basename(filetostrip_name + ".striparr." + filetostrip_ext)
            )

            celery_logger.info('Creating clean version of: "%s" in file "%s"' % (filetostrip, stripped_filepath))

            # check to see if the .striparr. file already exists
            pathexists = os.path.exists(stripped_filepath)
            pathisfile = os.path.isfile(stripped_filepath)

            if pathexists or pathisfile:
                celery_logger.error('file already exists: "%s", not overwriting' % (stripped_filepath))

            else:

                # prepare command line
                ffmpeg_strip_command = [
                    "ffmpeg",              # ffmpeg executable
                    "-i",                  # input file
                    filetostrip,           # the input file
                    ]

                # add banned metadata, setting each key to blank (eg: key= )
                for metadata_key in banned_metadata_keys:
                    ffmpeg_strip_command.append("-metadata")
                    ffmpeg_strip_command.append("%s=" % (metadata_key))

                # add remaining command line bits
                ffmpeg_strip_command += [
                     "-c:v", "copy",        # stream copy all video streams
                     "-c:a", "copy",        # stream copy all audio streams
                     "-c:s", "copy",        # stream copy all subtitle streams
                     stripped_filepath,     # output file
                    ]

                # run the command to create the stripped output file
                metadata_strip = subprocess.run(
                    ffmpeg_strip_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True
                    )

                # check output
                if metadata_strip.returncode != 0:
                    celery_logger.error('ffmpeg metadata strip failed: "%s"' % (metadata_strip.stderr))
                else:
                    # if output good, then overwrite original file
                    celery_logger.info('Overwriting: "%s" with clean file: "%s"' % (filetostrip, stripped_filepath))
                    shutil.move(stripped_filepath, filetostrip)
                    celery_logger.info('File is now clean: "%s"!' % (filetostrip))

        else:
            celery_logger.info('File already clean: "%s"' % (filetostrip))

    return "OK!"


# Listener task
@app.route('/', methods=['POST'])
def listener():

    if request.method == 'POST':

        # check to see if we've received a webhook from sonarr/radarr
        if request.is_json:

            # show the request JSON - useful for debugging
            # pprint(request.json)

            # If we've received a webhook with an eventType, then it has come from Sonarr/Radarr so process it
            if 'eventType' in request.json.keys():

                # Log test webhooks for ease of use/troubleshooting
                if request.json['eventType'].lower() == 'test':
                    if 'episodes' in request.json.keys():
                        app_logger.info('Received a Sonarr style webhook test')

                    if 'movie' in request.json.keys():
                        app_logger.info('Received a Radarr style webhook test')

                # We want to take action on "download" webhooks as this means a file has been imported
                elif request.json['eventType'].lower() == 'download':

                    # Process Sonarr style "download" webhook
                    if ('episodeFile' in request.json.keys()) and ('series' in request.json.keys()):
                        if ('relativePath' in request.json['episodeFile'].keys()) and ('path' in request.json['series'].keys()):

                            # build path
                            path_to_imported_file = os.path.join(
                                request.json['series']['path'],
                                request.json['episodeFile']['relativePath'],
                                )

                            # make sure the file exists
                            pathexists = os.path.exists(path_to_imported_file)
                            pathisfile = os.path.isfile(path_to_imported_file)

                            if pathexists and pathisfile:
                                app_logger.info('Enqueuing processing of file: "%s"' % (path_to_imported_file))
                                worker.delay(path_to_imported_file)

                            else:
                                app_logger.error('Could not access file: "%s", skipping' % (path_to_imported_file))

                        else:
                            app_logger.error('Received invalid JSON data from Sonarr')

                    # Process Radarr style "download" webhook
                    elif ('movieFile' in request.json.keys()) and ('movie' in request.json.keys()):
                        if ('relativePath' in request.json['movieFile'].keys()) and ('folderPath' in request.json['movie'].keys()):

                            # build path
                            path_to_imported_file = os.path.join(
                                request.json['movie']['folderPath'],
                                request.json['movieFile']['relativePath'],
                                )

                            # make sure the file exists
                            pathexists = os.path.exists(path_to_imported_file)
                            pathisfile = os.path.isfile(path_to_imported_file)

                            if pathexists and pathisfile:
                                app_logger.info('Enqueuing processing of file: "%s"' % (path_to_imported_file))
                                worker.delay(path_to_imported_file)

                            else:
                                app_logger.error('Could not access file: "%s", skipping' % (path_to_imported_file))

                        else:
                            app_logger.error('Received invalid JSON data from Radarr')

                # We received a webhook with unsupported type
                else:
                    app_logger.info("Received a webhook with event type '%s', ignoring" % (request.json['eventType']))

            # We received a webhook without an eventType
            else:
                app_logger.info("Received an webhook with no eventType, ignoring")

        # We received a POST with no JSON data
        else:
            app_logger.info("Received a non-JSON request, ignoring")

        sys.stdout.flush()

        return 'OK', 200

    else:
        abort(400)


if __name__ == '__main__':
    app.run()
