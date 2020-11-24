# mikenye/striparr

Strips "annoyance" metadata from items imported by [Sonarr](https://sonarr.tv) and [Radarr](https://radarr.video). Triggered via Webhook.

This utility will strip certain metadata tags from media container files, to allow media management systems (such as Plex) to name the files based on metadata collected from its media scanners.

This prevents, for example, a movie file being named such as `Title.year.quality.releasegroup`.

The metadata fields that Striparr will remove are:

* `title` field on the file
* `comment` field on the file

The streams within the media file are not touched.

## Disclaimer

Given this tool runs ffmpeg over your media files, there is the potential for it to break things.

I accept no responsibility for anything that happens through your use of this container or any of the code within it.

**USE AT YOUR OWN RISK!**

Having said that, if you have a problem with Striparr, I want to know about it. Please [log an issue on the project's GitHub page](https://github.com/mikenye/docker-striparr/issues) and I'll do my best to help you out. Please include your container logs and any other relevent technical information.

## How it works

1. Striparr is notified via webhook from Sonarr/Radarr that a new file has been imported to your media library
1. Striparr launches `ffmpeg` to perform a scan of the file, to identify metadata tags
1. If the file contains no annoyance metadata fields, Striparr does nothing further. If any of the annoyance metadata fields (listed above) are found:
    1. Striparr performs an `ffmpeg` stream copy for all audio, video and subtitle streams to a new file (`Original_Filename.striparr.Original_Extension`), setting the annoyance metadata fields to "" (blank).
    1. Striparr overwrites the old file with the new file

To keep the amount of disk IO reasonable, Striparr queues all requests up (in memory) and has a single worker process them sequentially. There will only ever be one ffmpeg process running at any time.

## Prerequisites

Sonarr and/or Radarr need to be able to contact this container on TCP port 40000.

## Up-and-Running

It is recommended that your Sonarr and/or Radarr containers (and any other supporting containers) be running on the same docker network as this container. This makes it simple to set up Webhooks. In the example below, Sonarr, Radarr and Striparr run in the network `arr`.

In order to strip metadata, your media volumes need to be mounted in exactly the same way as they are in your Sonarr and Radarr containers. Striparr requires no volume mounts for configuration, as there is no configuration outside of environment variables.

For example, if you run your Sonarr and Radarr containers like this:

```shell
docker run \
-d \
--name sonarr \
--restart=always \
--network=arr \
-e PUID=500 \
-e PGID=1000 \
-v /opt/Sonarr:/config \
-v /path/to/tv:/path/to/tv \
-v /path/to/downloads:/path/to/downloads \
-p 8989:8989 \
linuxserver/sonarr

docker run \
-d \
--name radarr \
--restart=always \
--network=arr \
-e PUID=500 \
-e PGID=1000 \
-v /opt/Radarr:/config \
-v /path/to/movies:/path/to/movies \
-v /path/to/downloads:/path/to/downloads \
-p 7878:7878 \
linuxserver/radarr
```

...then you would run your Striparr container like this:

```shell
docker run \
-d \
--name striparr \
--network=arr \
--restart=always \
-e PUID=500 \
-e PGID=1000 \
-v /path/to/tv:/path/to/tv \
-v /path/to/movies:/path/to/movies \
mikenye/striparr
```

*Important:*

* The volume mounts to the media from Sonarr and Radarr containers have also been presented to Striparr with exactly the same paths
* The environment variables PUID and PGID set on the Sonarr and Radarr container have also been set on Striparr with exactly the same values

A more elegant solution would be to have a `docker-compose.yml` file containing Sonarr, Radarr, their supporting containers, and Striparr all defined within the `docker-compose` file.

## Sonarr/Radarr Configuration

In order for Sonarr and/or Radarr to notify Striparr when files are downloaded (so Striparr can process them), you'll need to add a Webhook.

In both applications, the process to do this is as follows:

1. Go to "Settings" > "Connect"
1. Press the "+" button to add a new notification
1. In the "Add Notification" dialog that appears, scroll down and choose "Webhook"
1. Fill in the dialog as follows:
    * Set "Name" to `Striparr`
    * For Sonarr v2, ensure "On Download" is enabled (The others don't matter, but it is recommended to enable them all. Striparr ignores events it can't use.)
    * For Sonarr v3, ensure "On Upgrade" is enabled (The others don't matter, but it is recommended to enable them all. Striparr ignores events it can't use.)
    * For Radarr, ensure "On Download" is enabled (The others don't matter, but it is recommended to enable them all. Striparr ignores events it can't use.)
    * Set "URL" to `http://striparr:40000` (change this URL to suit your environment if required)
    * If you have a "Method" drop-down, select `POST`
    * Hit "Test". In the container log, it will log that it has received a test webhook (see below for example). Sonarr/Radar should show the test was successful. Then hit "Save".

The container logs showing that Striparr has received the test webooks will look as follows:

```text
[listener] [2019-10-15 03:54:04,337: INFO] [172.16.29.3] [Sonarr/3.0.3.644] Received a Sonarr style webhook test
[listener] [2019-10-15 03:54:55,475: INFO] [172.16.29.4] [Radarr/0.2.0.1358] Received a Radarr style webhook test
```

From this point forward, when Sonarr and/or Radarr download an item and import into your media library, Striparr will then strip the annoyance metadata from the item.

## Runtime Configuration Options

These environment variables should be set when starting the container:

* `TZ` - Your local timezone (optional, default: UTC)
* `PUID` - for the User ID that Striparr will run as (default: 1000)
* `PGID` - for the Group ID that Striparr will run as (default: 1000)

You must make sure that `PUID` and `PGID` match what you have set Sonarr and Radarr to use.

## Ports

Striparr listens for webhooks on TCP port 40000.

If the Striparr container is running on the same docker network as Sonarr/Radarr, there should be no need to map this port (ie, no need to add `-p 40000:40000` to the `docker run` command).

## Logging

Striparr logs to the container's `stdout`, and can be viewed with `docker logs [-f] container`.

It is recommended that you set up log rotation for your container logs, which is outlined here: <https://success.docker.com/article/how-to-setup-log-rotation-post-installation>

## Manually Processing Files

If you have existing files that you wish to process, you can use the `manually_process.py` script included within the container. When running this script, the syntax is:

```shell
docker exec -it striparr /manually_process.py /path/to/media/file
```

This script sends a webhook to Striparr (in the same way that Sonarr/Radarr would), thus you need to specify the *full path* to your media in the context of the container's file system. Relative paths won't work.

The easiest way to do this is to get a shell within the container (ie: `docker exec -it striparr sh`) and then use tab completion.

Example:

```text
docker-host$ docker exec -it striparr sh

<now on a shell within the container>

/ # /manually_process.py /path/to/movie/file.mkv
Request sent to striparr - see striparr log for details

/ # exit

<back on docker host>

docker-host$ docker logs striparr | tail -5

[listener] [2019-10-15 03:25:02,607: INFO] [127.0.0.1] [python-requests/2.22.0] Enqueuing processing of file: "/path/to/movie/file.mkv"
[worker] [2019-10-15 03:25:02,660: INFO/ForkPoolWorker-1] striparr.worker[2d5f7af2-ef03-11e9-81b4-2a2ae2dbcce4]: Checking: "/path/to/movie/file.mkv"
[worker] [2019-10-15 03:25:02,778: INFO/ForkPoolWorker-1] striparr.worker[2d5f7af2-ef03-11e9-81b4-2a2ae2dbcce4]: Creating clean version of: "/path/to/movie/file.mkv" in file "/path/to/movie/file.striparr.mkv"
[worker] [2019-10-15 03:25:26,277: INFO/ForkPoolWorker-1] striparr.worker[2d5f7af2-ef03-11e9-81b4-2a2ae2dbcce4]: Overwriting: "/path/to/movie/file.mkv" with clean file: "/path/to/movie/file.striparr.mkv"
[worker] [2019-10-15 03:25:29,379: INFO/ForkPoolWorker-1] striparr.worker[2d5f7af2-ef03-11e9-81b4-2a2ae2dbcce4]: File is now clean: "/path/to/movie/file.mkv"!
```

## Getting Help

Please feel free to [open an issue on the project's GitHub](https://github.com/mikenye/docker-striparr/issues).

I also have a [Discord channel](https://discord.gg/PrkZPgd), feel free to [join](https://discord.gg/PrkZPgd) and converse.
