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

    This sample mirrors LKL data from a Location Tracking Service or Location Tracking View into a standard feature service.
    That allows the user to support dynamic joins of data.
"""
import argparse
import logging
import logging.handlers
import traceback
import sys
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
    if gis.content.get(arguments.item_id):
        logger.info("Getting feature layer")
        item = gis.content.get(arguments.item_id)
        mirror_layer = item.layers[0]
        if arguments.lkl_layer_url:
            lkl_layer = FeatureLayer(url=arguments.lkl_layer_url)
        else:
            lkl_layer = gis.admin.location_tracking.last_known_locations_layer
            
        # Query LKL and mirror layer
        lkl_fset = lkl_layer.query('1=1', out_sr=3857)
        if len(lkl_fset) == 0:
            logger.info("No LKLs in your layer yet!")
            sys.exit(0)
        mirror_fset = mirror_layer.query('1=1', out_sr=3857)
        
        add_features = []
        update_features = []
        logger.info("Iterating through current LKL data")
        for feature in lkl_fset:
            found = False
            for mirror_feature in mirror_fset:
                # use "in" instead of == comparison due to the potential for brackets to be in the GUID field
                if mirror_feature.attributes[return_field_name(mirror_layer, "global_id")].lower() in feature.attributes["globalid"].lower():
                    found = True
                    break
            if found:
                update_features.append(feature)
            else:
                add_features.append(feature)
                
        logger.info("Posting updated data to mirrored layer")
        mirror_layer.edit_features(adds=add_features, updates=update_features, use_global_ids=True)
        logger.info("Completed!")
    else:
        logger.info("Item not found")
        

if __name__ == "__main__":
    # Get all of the commandline arguments
    parser = argparse.ArgumentParser("Python script which maintains an exact replica of your LKL layer in a separate feature service, so that data can be joined")
    parser.add_argument('-u', dest='username', help="The username to authenticate with", required=True)
    parser.add_argument('-p', dest='password', help="The password to authenticate with", required=True)
    parser.add_argument('-org', dest='org_url', help="The url of the org/portal to use", required=True)
    # Parameters for tracker
    parser.add_argument('-item-id', dest='item_id', required=True,
                        help="The item id of the layer you want the tracks to mirror to")
    parser.add_argument('-lkl-layer-url', dest='lkl_layer_url', default=None,
                        help="The last known location (LKL) layer (either location tracking service or tracks view) you'd like to use. Defaults to the Location Tracking Service LKL layer")
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