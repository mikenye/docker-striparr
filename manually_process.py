#!/usr/bin/env python

import argparse
import requests
import os

if __name__ == "__main__":

    # parse command line arguments
    parser = argparse.ArgumentParser(description="Manually process a video file")

    parser.add_argument('video_file',
        type=str,
        nargs='+',
        help='Video file',
        )

    args = parser.parse_args()

    for video_file in args.video_file:

        splitpath = os.path.split(video_file)

        request_json = {
            "eventType": "Download",
            "series": {
                "path": splitpath[0],
            },
            "episodeFile": {
                "relativePath": splitpath[1],
            },
        }

    r = requests.post('http://127.0.0.1:40000/', json=request_json)
    
    if r.status_code == 200:
        print("Request sent to striparr - see striparr log for details")
    else:
        print("Something went wrong")
