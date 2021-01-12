"""
   Copyright 2021 Esri
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.​

    This sample demonstrates how tracks can be exported from AGOL to CSV files
"""
import argparse
import datetime
import pendulum
import logging
import logging.handlers
import os
import traceback
import sys
from arcgis.gis import GIS


def initialize_logging(log_file=None):
    """
    Setup logging
    :param log_file: (string) The file to log to
    :return: (Logger) a logging instance
    """
    # initialize logging
    formatter = logging.Formatter(
        "[%(asctime)s] [%(filename)30s:%(lineno)4s - %(funcName)30s()][%(threadName)5s] [%(name)10.10s] [%(levelname)8s] %(message)s")
    # Grab the root logger
    logger = logging.getLogger()
    # Set the root logger logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    logger.setLevel(logging.DEBUG)
    # Create a handler to print to the console
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    sh.setLevel(logging.INFO)
    # Create a handler to log to the specified file
    if log_file:
        rh = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=10485760)
        rh.setFormatter(formatter)
        rh.setLevel(logging.DEBUG)
        logger.addHandler(rh)
    # Add the handlers to the root logger
    logger.addHandler(sh)
    return logger


def main(arguments):
    logger = initialize_logging(arguments.log_file)
    logger.info("Authenticating...")
    # Authenticate to ArcGIS Online
    gis = GIS(arguments.org_url,
              username=arguments.username,
              password=arguments.password,
              verify_cert=not arguments.skip_ssl_verification)
    if gis.properties['isPortal']:
        raise Exception("Export is not supported for the location tracking service with ArcGIS Enterprise")
    logger.info("Exporting...")
    tracks_item = gis.content.get(args.tracks_item)
    # Create date range using track age
    # Always export up through the last full day (intentionally excludes part of current day)
    start_date = pendulum.today(args.time_zone) - datetime.timedelta(days=args.track_age)
    end_date = pendulum.today(args.time_zone).at(23, 59, 59) - datetime.timedelta(days=1)
    # Export the tracks
    csv_item = tracks_item.export(f"tracks_{start_date.to_date_string()}_{end_date.to_date_string()}",
                                  export_format='CSV',
                                  parameters={
                                      "layers": [
                                          {
                                              "id": 0,
                                              "where": f"location_timestamp <= '{end_date.in_tz('UTC').to_datetime_string()}' AND "
                                                       f"location_timestamp >= '{start_date.in_tz('UTC').to_datetime_string()}'"
                                          }
                                      ]
                                  }
                                  )
    logger.info("Downloading...")
    # Download the CSV file
    save_path = os.path.dirname(os.path.abspath(args.output_file))
    file_name = os.path.basename(args.output_file)
    csv_item.download(save_path=save_path, file_name=file_name)
    # Delete the hosted CSV file
    csv_item.delete()
    logger.info("Complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "This exports tracks from a track view or location tracking service hosted in AGOL")
    parser.add_argument('-u', dest='username', help="The username to authenticate with", required=True)
    parser.add_argument('-p', dest='password', help="The password to authenticate with", required=True)
    parser.add_argument('-org', dest='org_url', help="The url of the org/portal to use", default="https://arcgis.com")
    parser.add_argument('-track-item', dest='tracks_item',
                        help="The location tracking service or track view item to export",
                        required=True)
    parser.add_argument('-track-age', dest='track_age', type=int, help="Number of previous full days of tracks to export", default=1)
    parser.add_argument('-time-zone', dest='time_zone', help="The timezone to use", default='UTC')
    parser.add_argument('-output-file', dest='output_file', help="The file to create", required=True)
    parser.add_argument('-log-file', dest='log_file', help="The log file to write to (optional)")
    parser.add_argument('--skip-ssl-verification',
                        dest='skip_ssl_verification',
                        action='store_true',
                        help="Verify the SSL Certificate of the server")
    args = parser.parse_args()
    try:
        main(args)
    except Exception as e:
        logging.getLogger().critical("Exception detected, script exiting")
        logging.getLogger().critical(e)
        logging.getLogger().critical(traceback.format_exc().replace("\n", " | "))
