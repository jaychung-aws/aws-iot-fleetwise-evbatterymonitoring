def handler(event, context):
    response = "Lambda invocation"
    print(response)
    return {
        'statusCode': 200,
        'body': response
    }


def query_timestream_in_timeframe(timeframe):
    # Querying Timestream Entries for specified timeframe
    print("Timestream Function")


def timestream_results_to_vehicle_list(timestream_results):
    # Receive List of Timestream results and create list of vehicles for inspection fleet
    print("Extract Vehicle List Function")


def create_update_inspection_fleetwise_fleet(vehicle_list):
    # Create or update the inspection fleet from the list of vehicles identified as having battery overheating issues
    print("Create Inspection Fleet Function")


def send_fleetoperator_notification(vehicle_list):
    # Send information to fleet operator about vehicles that need inspection
    print("Fleet Operator Notification Function")
