# Building Electric Vehicle Battery Monitoring solution with AWS IoT FleetWise

## Folder Structure

```text
├── cloud
│   ├── fleetwise                   <--- Template files and automation scripts used in Part 1/2
│   └── evbatteryhealthmonitoring   <--- CDK stack used to build all resources used in Part 2/2
├── dashboards                      <--- Grafana Dashboards utilized within the Blog Posts
├── images                          <--- Grafana Screenshots utilized in the Blog Post
├── queries                         <--- Timestream Queries
├── simulatedvehicle                <--- Everything that is needed to simulate the vehicles on Amazon EC2
└── README.md                       <--- this file
```

## Building an EV Battery Monitoring solution with AWS IoT FleetWise (Part 1/2)

This repository contains resources for the [blog post of the same name](https://aws.amazon.com/blogs/iot/building-an-ev-battery-monitoring-solution-with-aws-iot-fleetwise-part-1-2/):

- [AWS CloudFormation template for Electric Vehicle simulation](simulatedvehicle/ec2simulation/template.yaml) and [Troubleshooting guidelines](troubleshooting.md)
- [Examples of AWS CLI inputs to configure AWS IoT FLeetWise solution](cloud/fleetwise/cli-input-templates)
- [Sample Grafana dashboards to visualise vehicle data stored in Amazon Timestream](dashboards)


## Building an EV Battery Monitoring solution with AWS IoT FleetWise (Part 2/2)

This repository contains resources for the [blog post of the same name](TBD).

Please follow the following instructions.

1. Install and bootstrap the CDK:

   ```bash
   npm install -g aws-cdk
   # replace PROFILE_NAME with your specific AWS CLI profile that has username and region defined
   export CDK_DEPLOY_ACCOUNT=$(aws sts get-caller-identity --profile PROFILE_NAME --query Account --output text)
   # Set REGION to where the bootstrap resources will be deployed
   export CDK_DEPLOY_REGION=eu-central-1
   # replace PROFILE_NAME with your specific AWS CLI profile that has username and region defined
   cdk bootstrap aws://$CDK_DEPLOY_ACCOUNT/$CDK_DEPLOY_REGION
   ```

1. Clone the repository, change into the `evbatterymonitoring/` directory to build and deploy the CloudFormation stack:

   ```bash
   git clone https://github.com/aws-samples/aws-iot-fleetwise-evbatterymonitoring.git

   ```

1. Part of the Stack consists of a Lambda function that requires the latest version of Boto3. In order to do so, we will create a Lambda layer that contains exactly that. We will use the following lines of code to prepare that Lambda function.

   ```bash
   cd cloud/batteryhealthmonitoring/lambdalibs/python/
   pip3 install boto3 -t .
   cd ..
   zip -r python.zip python
   ```
   
1. Last but not least, let us deploy the cdk code. The CDK Stack requires three parameters: Your e-mail address for notifications, the name of the Timestream Database and Table.

   ```bash
   cd ..
   npm install
   npm run build
   cdk deploy --parameters fleetwisedatabase=<database-name> --parameters fleetwisetable=<table-name> --parameters batteryHealthMonitoringmail=<your-mail-address>
   ```
