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

    This sample allows cleanup of track points from a tracks layer based on a spatial relationship to polygon geometry.
    Requires being an admin to run this script
"""
import argparse
import logging
import logging.handlers
import traceback
import sys
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis import geometry


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


def form_donut(rings):
    for ring in rings:
        ring.reverse()
    # append the max extent as the clockwise outside ring
    rings.append([[-20037508.3427892, -20037508.3427892], [-20037508.3427892, 20037508.3427892], [20037508.3427892, 20037508.3427892],
                  [20037508.3427892, -20037508.3427892], [-20037508.3427892, -20037508.3427892]])
    return rings


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
    if not gis.properties.isPortal:
        logger.error("This script only works with ArcGIS Enterprise")
        sys.exit(0)

    logger.info("Getting location tracking service")
    try:
        tracks_layer = gis.admin.location_tracking.tracks_layer
    except Exception as e:
        logger.info(e)
        logger.info("Getting location tracking service failed - check that you are an admin and that location tracking is enabled for your organization")
        sys.exit(0)

    logger.info("Getting polygon layer")
    try:
        layer = FeatureLayer(url=args.layer_url, gis=gis)
        _ = layer._lyr_json
    except Exception as e:
        logger.info(e)
        logger.info("Layer could not be found based on given input. Please check your parameters again. Exiting the script")
        sys.exit(0)

    features = layer.query(where=args.where, out_sr=3857).features
    if len(features) > 0:
        geometries = [feature.geometry for feature in features]
        logger.info("Unifying geometry data")
        union_geometry = geometry.union(spatial_ref=3857, geometries=geometries, gis=gis)
        if args.symmetric_difference:
            union_geometry['rings'] = form_donut(union_geometry['rings'])
        intersect_filter = geometry.filters.intersects(union_geometry, sr=3857)
        logger.info("Querying features")
        x = tracks_layer.delete_features(geometry_filter=intersect_filter)
        logger.info("Deleting features")
        logger.info("Deleted: " + str(len(x['deleteResults'])) + " tracks")
        logger.info("Completed!")


if __name__ == "__main__":
    # Get all of the commandline arguments
    parser = argparse.ArgumentParser(
        "This sample allows cleanup of track points from a tracks layer based on a spatial relationship to polygon geometry")
    parser.add_argument('-u', dest='username', help="The username to authenticate with", required=True)
    parser.add_argument('-p', dest='password', help="The password to authenticate with", required=True)
    parser.add_argument('-org', dest='org_url', help="The url of the org/portal to use", required=True)
    # Parameters for tracker
    parser.add_argument('-layer-url', dest='layer_url',
                        help="The feature service URL for your layer with the geometry you want to use to delete track points",
                        required=True)
    parser.add_argument('-where', dest='where', help="Query conditions for polygons you want to use in your cleanup. Defaults to all (1=1)", default="1=1")
    parser.add_argument('--symmetric-difference', action='store_true', dest='symmetric_difference',
                        help="If provided, delete the tracks outside the polygon(s). If not provided, delete the tracks inside the polygon")
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
