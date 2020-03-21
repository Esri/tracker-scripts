## Mirror Last Known Locations layer (LKL) into a standard feature service

This script will copy data from a Last Known Locations (LKL) layer in a Location Tracking layer and mirror it into a standard feature service. 

As of April 2020, the Last Known Locations layer does not support dynamic joins, so the mirroring of data using this script may be useful if the user is trying to relate additional data to their last known locations data. Standard feature services support join features.

This script is designed to be run as a scheduled task, at whatever frequency you want to get updated LKL data from your Location Tracking layer. For example, the admin may set up this script to run every 10 minutes in order to get the latest data from the field.

For information on how to set up scheduled tasks, please see: https://www.esri.com/arcgis-blog/products/arcgis-pro/analytics/schedule-a-python-script-or-model-to-run-at-a-prescribed-time-2019-update/

and https://www.esri.com/arcgis-blog/products/product/analytics/scheduling-a-python-script-or-model-to-run-at-a-prescribed-time/

This script requires the use of a point layer that the data can be mirrored into. This layer would ideally share all the same fields as a standard LKL layer. We have a publicly shared layer with the requisite fields ready for you to import into your organization using the `clone_items` functionality in the Python API.

To import this layer into your organization (in AGOL), do:

```python
import arcgis
gis = arcgis.gis.GIS("https://arcgis.com","myusername","mypassword")
mirror_layer_item = gis.content.get("id")
gis.content.clone_items([mirror_layer_item])
```

This will create a standard feature service in your organization whose item id you can pass into this script. The layer you are cloning here is hosted in ArcGIS Online. To use this script in Enterprise, you also must prepare a layer to have mirrored data. Either

a. Follow the above steps to clone the layer into your AGOL account, and then use the copy_content solution in AGO Assistant to copy to Enterprise (follow steps outlined here: https://support.esri.com/en/technical-article/000018783)

OR

b. Create a blank point layer (Content > Create > Feature Layer > Build a layer > Points) and then add all the requisite fields to that layer. Ensure the field_name value is the same, not just the alias.

Location Tracking must be enabled for your organization to use this script. You must be either an admin or a track viewer in order to use this script.

Supports Python 3.6+

----

Other than the authentication arguments (username, password, org) the script uses the following parameters:

- -item_id - Item id in your portal of the feature service you want to mirror data into. See above for how to create this service. Required
- -lkl-layer-url \<tracks_layer_url\> - The URL to the LKL layer from a Track View you want to utilize (optional - defaults to the LKL layer in your location tracking service)
- -log-file \<logFile\> - The log file to use for logging messages

Example Usage 1  - Mirror LKL data from the lkl layer url into the layer with the listed item id
```python
python mirror_lkl_layer.py -u username -p password -org https://arcgis.com -item-id a05eee7b1cs5461db0e1ef1c1c4abe18 -lkl-layer-url https://locationservices9.arcgis.com/US6xjA1Nc8bW1aoA/arcgis/rest/services/f1087713d8934d5b8218dda736c26af4_Track_View/FeatureServer/1
```

## What it does

 1. First the script uses the provided credentials to authenticate with AGOL to get the required token
 2. Gets the LKL layer, which is either provided to the script or is pulled from the Location Tracking Service.
 3. Gets the layer that you are mirroring data into 
 4. Checks whether the LKL is already in the mirrored layer or is new
 5. Posts updates with both new and existing features using the `edit_features` functionality in the Python API