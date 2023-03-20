import json
import logging
import os
import boto3
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


fleetwise_database = os.environ.get("fleetwisedatabase")
fleetwise_table = os.environ.get("fleetwisetable")
sns_topic = os.environ.get("snstopic")
logger.info("FleetWiseDatabase: {} FleetWiseTable: {} ".format(fleetwise_database, fleetwise_table))

ts_query = boto3.client('timestream-query')
sns = boto3.client('sns')
fleetwise = boto3.client('iotfleetwise')

interval_in_hours = 1

measure_name = "Vehicle.DemoBrakePedalPressure"
measure_threshold = 1000

vehicle_ids = []


inspection_campaign = "inspection-batteryhealth-campaign"
inspection_fleet = "inspection-batteryhealth-fleet"

healthy_fleet = "healthy-fleet"


REAL_QUERY =  '          (  ' \
              '   SELECT time, vehicleName, measure_name, measure_value::double, VehicleVIN FROM ' + "FleetWiseDatabase " + '.' + "FleetWiseTable" + ' ' \
                                                                                                                                                     '   WHERE time between ago(60m) and now()  ' \
                                                                                                                                                     '   AND measure_name=\'EVBatterySample.BMS.BatteryPack01MaxAvgModuleTemperature\'  ' \
                                                                                                                                                     '   and measure_value::double >119  ' \
                                                                                                                                                     '   Order BY time limit 10  ' \
                                                                                                                                                     '          )  '

# TODO add distinct
TEST_QUERY = 'SELECT distinct vehicleId FROM \"' + fleetwise_database + '\".\"' + fleetwise_table + '\" ' \
                                                                                                    '   Where measure_name=\'' + measure_name + '\' AND measure_value::double > ' + str(measure_threshold) + ' LIMIT 30'


def handler(event, context):
    logger.info("Event received by function: {}".format(json.dumps(event)))

    query_timestream_in_timeframe_and_create_vehiclelist()
    number_of_vehicles_count_list = create_update_inspection_fleetwise_fleet()

    send_fleetoperator_notification(number_of_vehicles_count_list[0], number_of_vehicles_count_list[1])


def query_timestream_in_timeframe_and_create_vehiclelist():
    # Querying Timestream Entries for specified timeframe
    logger.info("Timestream Function")

    response = ts_query.describe_endpoints()
    logger.info("Response describe_endpoints: {}".format(response))

    response = ts_query.query(QueryString=TEST_QUERY)
    for key in response['Rows']:
        vehicle_ids.append(key['Data'][0]['ScalarValue'])

    logger.info("Vehicle List from Timestream: {}".format(vehicle_ids))


def create_update_inspection_fleetwise_fleet():
    # Create or update the inspection fleet from the list of vehicles identified as having battery overheating issues
    print("Create Inspection Fleet Function")
    count_vehicles_in_inspection_fleet = 0

    try:
        fleetwise.get_fleet(fleetId=inspection_fleet)
    except Exception as e:
        logger.info("Inspection fleet doesn't exist")
        signal_catalog_information = fleetwise.list_signal_catalogs(maxResults=1)
        signal_catalog_information = signal_catalog_information["summaries"][0]["arn"]
        logger.info("Existing Signal Calalog ARN: {}".format(signal_catalog_information))
        fleetwise.create_fleet(fleetId=inspection_fleet, description='Inspection Fleet to get better details about vehicles.',
                               signalCatalogArn=signal_catalog_information)

        # Create inspection campaign

    vehicles_in_inspection_fleet = fleetwise.list_vehicles_in_fleet(fleetId=inspection_fleet)
    vehicles_in_inspection_fleet = vehicles_in_inspection_fleet["vehicles"]
    logger.info("Vehicles in inspection fleet: {}".format(json.dumps(vehicles_in_inspection_fleet)))

    vehicles_in_healthy_fleet = fleetwise.list_vehicles_in_fleet(fleetId=healthy_fleet)
    vehicles_in_healthy_fleet = vehicles_in_healthy_fleet["vehicles"]

    # Remove all Vehicle IDs returned from Timestream, so we have a list of vehicles to add to the inspection fleet
    for vehicle in vehicle_ids:
        # if inspection fleet isn't empty
        if vehicles_in_inspection_fleet and vehicle in vehicles_in_inspection_fleet:
            vehicle_ids.remove(vehicle)
            count_vehicles_in_inspection_fleet += 1
        else:
            # Vehicle isn't in inspection fleet yet, so we associate the vehicle now
            fleetwise.associate_vehicle_fleet(vehicleName = vehicle, fleetId = inspection_fleet)
            # if the vehicle was in the healthy fleet, remove it
            if vehicle in vehicles_in_healthy_fleet:
                fleetwise.disassociate_vehicle_fleet(vehicleName=vehicle, fleetId=healthy_fleet)

    return [count_vehicles_in_inspection_fleet, len(vehicle_ids)]


def send_fleetoperator_notification(number_already_in_list, number_added_to_list):
    # Send information to fleet operator about vehicles that need inspection
    logger.info("Fleet Operator Notification Function")

    message = "This is an information message about the current fleet health.\nCurrently {} vehicles are already part of the inspection campaign" \
              "due to a Cell Temperature above {} degrees celsius. Also, this was the reason for {} new vehicles being added to the inspection campaign" \
              "Please view your Grafana Dashboard to receive more detailed information".format(number_already_in_list, measure_threshold, number_added_to_list)


    sns.publish(TopicArn=sns_topic, Message=message, Subject="Battery Health Inspection Update")
