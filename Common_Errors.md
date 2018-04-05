## Common Errors

Here are some common errors you may experience while running this solution

### Glue Data Catalog connections fail to connect
As part of solution deployment, while creating the Glue Data Catalog connection objects, the Cloudformation script calls Redshift describe-clusters to get the VPC, subnet, database information. The user name and password details are obtained from the AWS Systems Manager parameter store. If any of those details change after the solution is deployed, go to AWS Glue -> Data catalog -> Connections and change the Glue connections to reflect the right values. Few areas to verify are:
* verify that the database displayed in AWS Console Redshift cluster detailed view is the right database
* verify that the subnet and security group details are rightly populated in the Glue connections
* verify that the user name and password details are accurate

### Glue Data Catalog connection user name and password have _tempuser_ and _temppassword_ values
The solution deployment CloudFormation template originally creates the connection objects for each export enabled Redshift cluster with _tempuser_ and _temppassword_ as the user name and password respectively. However, as detailed in the blog post once you complete the post deployment step on updating the parameters _redshift_query_logs.<<cluster_name>>.user_ and _redshift_query_logs.<<cluster_name>>.password_  in the AWS Systems Manager parameter store with the right values, the Lambda function _InvokeGlueETLToExportRedshiftLogs_ will update the Glue connection user name and password with the right values from the parameter store for the respective Redshfit cluseter. Based on the CloudWatch event rule _InvokeGlueETLToExportRedshiftLogsScheduledRule_ you just have to wait for few minutes (10 minutes default) for these values to update. No troubleshooting is required from your side for this observation, the solution will automatically compare the user name and password in the paramter store with the connection object and will update accordingly

### CONNECTION_LIST_CONNECTION_WITH_AZ_NULL error message

 In some random cases, Glue ETL jobs created as part of this solution fail with in seconds with message _CONNECTION_LIST_CONNECTION_WITH_AZ_NULL_. This is usually because of missing 'AvailabilityZone' parameter while creating or updating connections. The solution by default takes care of this issue. However if you observe this issue for any manual AWS Glue data catalog connections you created, following steps will help resolve this issue:
 * Go to the AWS Glue -> Data Catalog -> Databases -> Connections and verify that the connections used by the respective Glue ETL jobs are working by clicking on 'Test Connection'
 * If the Glue connections fail follow the steps laid out above in the first issue

 ### Empty Dataset or missing partitions while querying Athena tables
 Run ```msck repair table <tablename>``` in the Athena console to refresh the metastore with latest partitions
