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
import math
import traceback
import sys
from arcgis.apps import workforce
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


def get_simple_distance(coords1, coords2):
    """
    Calculates the simple distance between two x,y points
    :param coords1: (Tuple) of x and y coordinates
    :param coords2: (Tuple) of x and y coordinates
    :return: (float) The distance between the two points
    """
    return math.sqrt((coords1[0] - coords2[0]) ** 2 + (coords1[1] - coords2[1]) ** 2)


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
    edit_field = return_field_name(layer, name_to_check="Editor")
    layer_query_string = ""
    if workers:
        for worker in workers:
            if layer_query_string != "":
                layer_query_string = layer_query_string + " OR "
            layer_query_string = layer_query_string + "{} = '{}'".format(edit_field, worker)
    else:
        logger.info("Please pass at least one worker user_id")
        sys.exit()
    # These are the features whose corresponding editors we will check
    features_to_check = layer.query(where=layer_query_string, out_sr=3857).features
    if len(features_to_check) == 0:
        logger.info("No features found to check. Please check the user_id's that you have passed")
        sys.exit(0)
    
    # Get field names, whether AGOL or Enterprise, to use
    accuracy_field = return_field_name(tracks_layer, name_to_check="horizontal_accuracy")
    creator_field = return_field_name(tracks_layer, name_to_check="created_user")
    timestamp_field = return_field_name(tracks_layer, name_to_check="location_timestamp")
    
    # Find invalid features
    invalid_features = []
    logger.info("Finding invalid features")
    for feature in features_to_check:
        # Get coordinates of the assignment
        try:
            start_coords = (feature.geometry["x"], feature.geometry["y"])
        except Exception as e:
            logger.info(e)
            logger.info("Check that you are using point geometry for your feature layer")
            sys.exit(0)
        # The date to check
        try:
            # date field may not be populated
            if feature.attributes[field_name]:
                date_to_check = datetime.datetime.utcfromtimestamp(feature.attributes[field_name] / 1000)
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
        check_track_query = "{} < '{}'".format(timestamp_field, end_date.strftime('%Y-%m-%d %H:%M:%S'))
        check_tracks = tracks_layer.query(where=check_track_query, return_count_only=True)
        if check_tracks == 0:
            logger.info("For this feature, no tracks exist for the time period in your LTS. Ensure that tracks have been retained for the time period you're verifying")
            continue
        
        # Make a query string to select location by the worker during the time period
        loc_query_string = "{} = '{}' AND {} >= '{}' AND {} <= '{}' AND {} <= {}" \
            .format(creator_field, feature.attributes[edit_field],
                    timestamp_field,
                    start_date.strftime('%Y-%m-%d %H:%M:%S'), timestamp_field,
                    end_date.strftime('%Y-%m-%d %H:%M:%S'), accuracy_field,
                    min_accuracy)
        # Query the feature layer
        locations_to_check = tracks_layer.query(where=loc_query_string, out_sr=3857, order_by_fields=timestamp_field + " ASC").features
        
        # Bool to see if this assignment is valid or not
        is_valid = False
        for location in locations_to_check:
            # Make a list of coordinate pairs to get the distance of
            coords = [(location.geometry["x"], location.geometry["y"])]
            accuracy = float(location.attributes[accuracy_field])
            # If we include the accuracy, we need to make four variations (+- the accuracy)
            coords.append((location.geometry["x"] + accuracy,
                           location.geometry["y"] + accuracy))
            coords.append((location.geometry["x"] + accuracy,
                           location.geometry["y"] - accuracy))
            coords.append((location.geometry["x"] - accuracy,
                           location.geometry["y"] + accuracy))
            coords.append((location.geometry["x"] - accuracy,
                           location.geometry["y"] - accuracy))
            distances = [get_simple_distance(start_coords, coordinates) for coordinates in coords]
            # if any of the distances is less than the threshold then this assignment is valid
            if any(distance < dist_tolerance for distance in distances):
                is_valid = True
                break
        if not is_valid:
            invalid_features.append(feature)
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
    if arguments.project_id and arguments.layer_url:
        logger.info("Please use either project id or layer url as your work order layer, not both")
        sys.exit(0)
    elif arguments.project_id:
        item = gis.content.get(arguments.project_id)
        layer = workforce.Project(item).assignments_layer
    elif arguments.layer_url:
        layer = FeatureLayer(arguments.layer_url)
    else:
        logger.info("Please provide either a portal id for your Workforce project or a feature service URL for your survey/collector layer")
        sys.exit(0)
    try:
        tracks_layer = gis.admin.location_tracking.tracks_layer
    except Exception as e:
        logger.info(e)
        logger.info("Getting location tracking service failed - check that you are an admin and that location tracking is enabled for your organization")
        sys.exit(0)
        
    # Return invalid work orders
    workers = arguments.workers.split(",")
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
            logger.info("The user who last edited the feature with OBJECTID {} was not within the desired accuracy for the field you are checking".format(work_order.attributes[return_field_name(layer, "objectid")]))

    
if __name__ == "__main__":
    # Get all of the commandline arguments
    parser = argparse.ArgumentParser("Check that the worker was nearby when editing features")
    parser.add_argument('-u', dest='username', help="The username to authenticate with", required=True)
    parser.add_argument('-p', dest='password', help="The password to authenticate with", required=True)
    parser.add_argument('-org', dest='org_url', help="The url of the org/portal to use", required=True)
    # Parameters for tracker
    parser.add_argument('-workers', dest='workers', help="Comma separated list of user_id's for the workers to check")
    parser.add_argument('-field-name', dest='field_name', default="EditDate",
                        help="The date field name within the Survey or Collector layer you use to integrate with Tracker. Use actual field name, not alias. Default is EditDate (for AGOL)")
    parser.add_argument('-project-id', dest='project_id', help="The id of the project whose assignments must be verified",
                        default=None)
    parser.add_argument('-layer-url', dest='layer_url',
                        help="The feature service URL for your Survey or Collector layer with features to be verified",
                        default=None)
    parser.add_argument('-log-file', dest='log_file', help="The log file to write to")
    parser.add_argument('-time-tolerance', dest='time_tolerance',
                        help="The tolerance (in minutes) to check a given date field vs location", type=int, default=10)
    parser.add_argument('-distance-tolerance', dest='distance_tolerance', type=int, default=100,
                        help='The distance tolerance to use (meters - based on SR of Assignments FL)')
    parser.add_argument('-min-accuracy', dest='min_accuracy', default=50,
                        help="The minimum accuracy to use (meters - based on SR of Assignments FL)")
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