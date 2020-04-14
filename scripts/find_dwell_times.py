"""
   Copyright 2020 Esri
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.​

    This sample reports work orders (assignments, features, surveys) that were edited or created while the user was not close by using Tracker data
    You must be an admin in your organization to use this script
"""
import argparse
import datetime
import logging
import logging.handlers
import pandas
import pendulum
import traceback
import sys
import arcgis
from arcgis.gis import GIS
from arcgis.features import FeatureLayer


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
    # initialize logger
    logger = initialize_logging(arguments.log_file)
    # Create the GIS
    logger.info("Authenticating...")
    # First step is to get authenticate and get a valid token
    gis = GIS(arguments.org_url,
              username=arguments.username,
              password=arguments.password,
              verify_cert=not arguments.skip_ssl_verification)
    
    # Get the feature layer
    logger.info("Getting polygon feature layer")
    layer = FeatureLayer(arguments.layer_url)
    logger.info("Getting tracks layer")
    if arguments.tracks_layer_url:
        tracks_layer = FeatureLayer(url=arguments.tracks_layer_url)
    else:
        try:
            tracks_layer = gis.admin.location_tracking.tracks_layer
        except Exception as e:
            logger.info(e)
            logger.info(
                "Getting location tracking service failed - check that you are an admin and that location tracking is enabled for your organization")
            sys.exit(0)
    
    logger.info("Building query")
    tracks_query = ""
    if args.start_date:
        local_start_date = pendulum.from_format(args.start_date, "MM/DD/YYYY hh:mm:ss", tz=args.timezone,formatter='alternative').in_tz('UTC').format("%Y-%m-%d %H:%M:%S")
        if tracks_query:
            tracks_query = tracks_query + " AND "
        tracks_query = tracks_query + f"location_timestamp > TIMESTAMP '{local_start_date}'"
    if args.end_date:
        local_end_date = pendulum.from_format(args.end_date, "MM/DD/YYYY hh:mm:ss", tz=args.timezone,formatter='alternative').in_tz('UTC').format("%Y-%m-%d %H:%M:%S")
        if tracks_query:
            tracks_query = tracks_query + " AND "
        tracks_query = tracks_query + f"location_timestamp < TIMESTAMP '{local_end_date}'"
    
    logger.info("Querying tracks layer")
    polygon_features = layer.query(where=args.where, out_sr=3857)
    for feature in polygon_features:
        if args.workers:
            workers = arguments.workers.replace(" ", "").split(",")
            for worker in workers:
                # check if empty
                if tracks_query:
                    tracks_query = tracks_query + " AND "
                tracks_query = tracks_query + f"created_user = '{worker}'"
        intersect_filter = arcgis.geometry.filters.intersects(geometry=feature.geometry, sr=3857)
        intersect_features = tracks_layer.query(where=tracks_query, geometry_filter=intersect_filter, out_sr=3857, order_by_fields="location_timestamp ASC")
        if len(intersect_features) > 0:
            start_date = None
            end_date = None
            for i_feature in intersect_features:
                if start_date is None:
                    start_date = pendulum.from_timestamp((i_feature.attributes["location_timestamp"])/1000)
                last_end_date = end_date
                end_date = pendulum.from_timestamp((i_feature.attributes["location_timestamp"])/1000)
                if end_date.diff(last_end_date).in_seconds() > 120 and start_date is not end_date:
                    logger.info("")
        else:
            logger.info("No tracks found matching your query!")


if __name__ == "__main__":
    # Get all of the commandline arguments
    parser = argparse.ArgumentParser("Check that the worker was nearby when editing features")
    parser.add_argument('-u', dest='username', help="The username to authenticate with", required=True)
    parser.add_argument('-p', dest='password', help="The password to authenticate with", required=True)
    parser.add_argument('-org', dest='org_url', help="The url of the org/portal to use", required=True)
    # Parameters for tracker
    parser.add_argument('-layer-url', dest='layer_url',
                        help="The feature service URL for the polygons you want to check intersecting geometry with",
                        required=True)
    parser.add_argument('-where', dest='where', help="Where clause on polygon layer", default="1=1")
    parser.add_argument('-workers', dest='workers', help="Comma separated list of user_id's for the workers to check. If not provided, check all workers", default=None)
    parser.add_argument('-start-date', dest='start_date',
                        help="If a worker has not been updated at or after this date, change its status to not working. Either int (in minutes from UTC now) or MM/DD/YYYY hh:mm:ss format")
    parser.add_argument('-end-date', dest='end_date',
                        help="If a worker has not been updated at or after this date, change its status to not working. Either int (in minutes from UTC now) or MM/DD/YYYY hh:mm:ss format")
    parser.add_argument('-timezone', dest='timezone', default="UTC", help="The timezone for the cutoff date")
    parser.add_argument('-log-file', dest='log_file', help="The log file to write to (optional)")
    parser.add_argument('-tracks-layer-url', dest='tracks_layer_url', default=None,
                        help="The tracks layer (either location tracking service or tracks view) you'd like to use. Defaults to the Location Tracking Service tracks layer")
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