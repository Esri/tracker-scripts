## Check the location and time that a worker edited a feature

This script checks the location and time of when a Workforce assignment, Collector feature, or Survey123 survey was edited against the location of the worker at that same time using Tracker. It is designed to find out if workers are completing work orders without visiting the location.
It reports features where the user might not have visited to the log file or standard ouptut. The user will insert the feature layer to be validated, the worker names they would like to check, and a date field they want to perform validation against.

For example, an admin may use this script to verify whether or not a user was nearby when they completed a Workforce assignment by passing the "completedDate" field and assignments feature layer into the script. 

Location Tracking must be enabled for your organization to use this script. You must be either an admin or a track viewer who can view the tracks of each worker whose work you'd like to verify in order to use this script.

Supports Python 3.6+

----

Other than the authentication arguments (username, password, org) the script uses the following parameters:

- -workers \<worker1\>,<worker2\> ,<workern\> - A comma-separated list of specific workers to check
- -field-name <field_name> - The date field name within the feature layer you use to integrate with Tracker. Use actual field name, not alias. Default is EditDate (for AGOL)
- -layer-url <layer_url> - The feature service URL for your Survey, Collector, or Workforce assignments feature layer with features to be validated. This is required.
- -time-tolerance \<timeTol\> - The time tolerance to use when checking workers locations. This value is used to provide a range around the time when the assignment was completed (optional - defaults to 10 minutes)
- -distance-tolerance \<distTol\> - The distance tolerance to use when checking if a worker completed the assignment at the assignment location (optional - defaults to 100 (m)). The units are in meters.
- -min-accuracy \<minAccuracy\> - The minimum accuracy required when querying worker locations (optional - defaults to 50 (m)). The units are in meters.
- -tracks-layer-url \<tracks_layer_url\> - The URL to the track view layer you want to utilize (optional - defaults to the tracks layer in your location tracking service)
- -log-file \<logFile\> The log file to use for logging messages

Example Usage:
```python
python check_completion_location.py -u username -p password -org https://.arcgis.com -workers admin_tracker,user_james,user_aaron -field-name completedDate -time-tolerance 10 -distance-tolerance 100 -layer-url https://services.arcgis.com/a910db6b36ff4066a3d4131fccc3da9b/arcgis/rest/services/assignments_ad9af2fc00314fa79ce79ec7d7317acc/FeatureServer/0
```

## What it does

 1. First the script uses the provided credentials to authenticate with AGOL to get the required token
 2. Then the feature layer to be validated is fetched
 3. Then the location feature layers are fetched
 4. For all features that were last edited by a worker in your provided list of workers, check if worker was within range when your provided field was edited (timeTol, distTol, and minAccuracy to determine whether in range)