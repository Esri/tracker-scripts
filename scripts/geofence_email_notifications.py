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

"""
import argparse
import logging
import logging.handlers
import traceback
import pendulum
import sys
import yagmail
import arcgis
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.geometry import Point



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
    
    if arguments.lkl_layer_url:
        lkl_layer = FeatureLayer(url=arguments.lkl_layer_url, gis=gis)
    else:
        logger.info("Please pass an LKL layer url!")
        sys.exit(0)
    
    logger.info("Checking LKL values exist")
    # Query LKL and check features exist
    lkl_fset = lkl_layer.query('1=1')
    if len(lkl_fset) == 0:
        logger.info("No LKLs in your layer yet!")
        sys.exit(0)
    
    logger.info("Buffering around the provided lat/long ")
    pt = Point({"x": args.longitude, "y": args.latitude, "spatialReference": {"wkid": 4326}})
    buffer = arcgis.geometry.buffer([pt], distances=args.distance_tolerance, in_sr=4326, out_sr=4326, unit=9001)
    buffer_filter = arcgis.geometry.filters.intersects(buffer[0], sr=4326)
    results = lkl_layer.query(geometry_filter=buffer_filter).features
    if len(results) > 0:
        # ensure yagmail is set up before you hit this part of the code: https://github.com/kootenpv/yagmail#username-and-password
        yag = yagmail.SMTP(args.gmail_user)
        recipient_emails = arguments.recipient_emails.replace(" ", "").split(",")
        body = ""
        users = []
        for result in results:
            users.append(result.attributes['created_user'])
            body = body + f"As of {pendulum.from_timestamp(result.attributes['last_edited_date'] / 1000)}, the user {result.attributes['created_user']} is in the area that is {args.distance_tolerance} meters around ({args.latitude},{args.longitude})\n"
        subject = str(users)[1: -1] + " in geofence"
        yag.send(to=recipient_emails, subject=subject, contents=body)
        ogger.info("Email sent")
    else:
        logger.info("No users in the geofence")
    logger.info("Completed!")


if __name__ == "__main__":
    # Get all of the commandline arguments
    parser = argparse.ArgumentParser("Email if a Tracker user is in a geofence")
    parser.add_argument('-u', dest='username', help="The username to authenticate with", required=True)
    parser.add_argument('-p', dest='password', help="The password to authenticate with", required=True)
    parser.add_argument('-org', dest='org_url', help="The url of the org/portal to use", required=True)
    # Parameters for tracker
    parser.add_argument('-lkl-layer-url', dest='lkl_layer_url', required=True,
                        help="The last known location (LKL) layer (either location tracking service or tracks view) you'd like to use. This URL should end in /1")
    parser.add_argument('-latitude', dest='latitude',type=float,required=True, help="Latitude of the point you want to buffer")
    parser.add_argument('-longitude', dest='longitude',type=float, required=True, help="Longitude of the point you want to buffer")
    parser.add_argument('-distance-tolerance', dest='distance_tolerance', type=int, default=100,
                        help='The distance tolerance to use (in meters)')
    parser.add_argument('-gmail-username', dest='gmail_user', type=str, required=True, help='The Gmail username you are going to send notifications from')
    parser.add_argument('-recipient-emails', dest='recipient_emails', type=str, help="Comma separated list of emails for the notifications to go out to")
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