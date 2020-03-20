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


def return_field_name(layer, name_to_check):
    for field in layer.properties.fields:
        if field['name'].replace("_","").lower() == name_to_check.replace("_","").lower():
            return field['name']


def get_invalid_work_orders(layer, field_name, time_tolerance, dist_tolerance, min_accuracy, workers, tracks_layer, logger):
    """
    Finds all invalid work orders by comparing a date vs. worker location
    """
    # Query for all features last edited by a worker in your list
    logger.info("Querying for features edited by a worker in your list")
    editor_field = return_field_name(layer, name_to_check="Editor")
    object_id_field = return_field_name(layer, name_to_check="OBJECTID")
    layer_query_string = ""
    if workers:
        for worker in workers:
            if layer_query_string != "":
                layer_query_string = layer_query_string + " OR "
            layer_query_string = layer_query_string + f"{editor_field} = '{worker}'"
    else:
        logger.info("Please pass at least one worker user_id")
        sys.exit()
    # These are the features whose corresponding editors we will check
    sr = {'wkid': 3857, 'latestWkid': 3857}
    features_df = layer.query(where=layer_query_string, out_sr=sr, return_all_records=True, as_df=True)
    if len(features_df.index) == 0:
        logger.info("No features found to check. Please check the user_id's that you have passed")
        sys.exit(0)
    
    # buffer features to use as geometry filter
    features_df["BUFFERED"] = features_df["SHAPE"].geom.buffer(dist_tolerance + min_accuracy)
    features_df.spatial.set_geometry("BUFFERED")
    features_df.spatial.sr = sr
    
    # Set field names
    accuracy_field = "horizontal_accuracy"
    creator_field = "created_user"
    timestamp_field = "location_timestamp"
    
    # Find invalid features
    invalid_features = []
    logger.info("Finding invalid features")
    for index, row in features_df.iterrows():
        # The date to check
        try:
            # date field may not be populated
            if not pandas.isnull(row[field_name]):
                date_to_check = row[field_name]
            else:
                continue
        except Exception as e:
            logger.info("Check that the exact field name exists in the feature layer")
            logger.info(e)
            sys.exit(0)
        
        # Add/Subtract some minutes to give a little leeway
        start_date = date_to_check - datetime.timedelta(minutes=time_tolerance)
        end_date = date_to_check + datetime.timedelta(minutes=time_tolerance)
        
        # Check there are actually tracks in your LTS in that time period. Otherwise, go to next feature
        check_track_query = f"{timestamp_field} < '{end_date.strftime('%Y-%m-%d %H:%M:%S')}'"
        check_tracks = tracks_layer.query(where=check_track_query, return_count_only=True)
        if check_tracks == 0:
            logger.info("For this feature, no tracks exist for the time period in your LTS. Ensure that tracks have been retained for the time period you're verifying")
            continue
        
        # Make a query string to select location by the worker during the time period
        loc_query_string = f"{creator_field} = '{row[editor_field]}' " \
            f"AND {timestamp_field} >= timestamp '{start_date.strftime('%Y-%m-%d %H:%M:%S')}' " \
            f"AND {timestamp_field} <= timestamp '{end_date.strftime('%Y-%m-%d %H:%M:%S')}' " \
            f"AND {accuracy_field} <= {min_accuracy}" \

        # Generate geometry filter, query the feature layer
        geom_filter = arcgis.geometry.filters.intersects(row['BUFFERED'], sr=sr)
        tracks_within_buffer = tracks_layer.query(where=loc_query_string, geometry_filter=geom_filter, return_count_only=True)
        if tracks_within_buffer == 0:
            invalid_features.append(row[object_id_field])
    return invalid_features


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
    logger.info("Getting feature layer")
    layer = FeatureLayer(arguments.layer_url)
    logger.info("Getting tracks layer")
    if arguments.tracks_layer_url:
        tracks_layer = FeatureLayer(url=arguments.tracks_layer_url)
    else:
        try:
            tracks_layer = gis.admin.location_tracking.tracks_layer
        except Exception as e:
            logger.info(e)
            logger.info("Getting location tracking service failed - check that you are an admin and that location tracking is enabled for your organization")
            sys.exit(0)
        
    # Return invalid work orders
    workers = arguments.workers.replace(" ", "").split(",")
    invalid_work_orders = get_invalid_work_orders(layer,
                                                  arguments.field_name,
                                                  arguments.time_tolerance,
                                                  arguments.distance_tolerance,
                                                  arguments.min_accuracy,
                                                  workers,
                                                  tracks_layer,
                                                  logger)
    if len(invalid_work_orders) == 0:
        logger.info("No features found that match the criteria you've set")
    else:
        for work_order in invalid_work_orders:
            logger.info(f"The user who last edited the feature with OBJECTID {work_order} was potentially not within the distance tolerance when updating the field {arguments.field_name}")

    
if __name__ == "__main__":
    # Get all of the commandline arguments
    parser = argparse.ArgumentParser("Check that the worker was nearby when editing features")
    parser.add_argument('-u', dest='username', help="The username to authenticate with", required=True)
    parser.add_argument('-p', dest='password', help="The password to authenticate with", required=True)
    parser.add_argument('-org', dest='org_url', help="The url of the org/portal to use", required=True)
    # Parameters for tracker
    parser.add_argument('-workers', dest='workers', help="Comma separated list of user_id's for the workers to check")
    parser.add_argument('-field-name', dest='field_name', default="EditDate",
                        help="The date field name within the feature layer you use to integrate with Tracker. Use actual field name, not alias. Default is EditDate (for AGOL)")
    parser.add_argument('-layer-url', dest='layer_url',
                        help="The feature service URL for your Survey, Collector, or Workforce assignments feature layer with features to be verified",
                        required=True)
    parser.add_argument('-log-file', dest='log_file', help="The log file to write to (optional)")
    parser.add_argument('-time-tolerance', dest='time_tolerance',
                        help="The tolerance (in minutes) to check a given date field vs location", type=int, default=10)
    parser.add_argument('-distance-tolerance', dest='distance_tolerance', type=int, default=100,
                        help='The distance tolerance to use (in meters)')
    parser.add_argument('-min-accuracy', dest='min_accuracy', default=50,
                        help="The minimum accuracy to use (in meters)")
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