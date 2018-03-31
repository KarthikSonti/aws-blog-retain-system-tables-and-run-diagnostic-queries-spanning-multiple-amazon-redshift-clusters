import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
import time
import pg8000
import boto3
import re
from decimal import *
import extract_rs_query_logs_functions as functions


## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['TempDir', 'JOB_NAME','REGION','CLUSTER_ENDPOINT'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)
job_configs={}
job_configs.update(args)
clusterId= re.search('jdbc:redshift://(.+?)\..*',args['CLUSTER_ENDPOINT']).group(1)
job_configs.update(functions.getJobConfigurations(clusterId,job_configs))
job_configs['CLUSTER_ID']=clusterId
tempDir=args['TempDir']
s3Prefix=job_configs['s3_prefix']
credentials=boto3.Session().get_credentials()
job_configs['aws_access_key_id'] = credentials.access_key
job_configs['aws_secret_access_key'] = credentials.secret_key
job_configs['aws_session_token'] = credentials.token
job_configs.update(args)
job_configs['jdbcURL']="{}?user={}&password={}".format(args['CLUSTER_ENDPOINT'],job_configs['user'],job_configs['password'])
job_configs['region_name']=boto3.session.Session().region_name
job_configs['spark_session']=spark


#### Query Text  #####

stlQueryLastProcessedTSValue= functions.getLastProcessedTSValue(trackingEntry=clusterId+"_stl_query",job_configs=job_configs)
returnDF=functions.runQuery(query="select '{}' as clusterId,trunc(a.starttime) as startDate,b.* from stl_querytext b , stl_query a where a.query=b.query and a.endtime > '{}'".format(clusterId,stlQueryLastProcessedTSValue),tableName="stl_querytext",job_configs=job_configs)
functions.saveToS3(dataframe=returnDF,s3Prefix=s3Prefix,tableName="stl_querytext",partitionColumns=["clusterid","startdate"],job_configs=job_configs)

#### Explain #####

stlQueryLastProcessedTSValue= functions.getLastProcessedTSValue(clusterId+"_stl_query",job_configs)
returnDF=functions.runQuery("select '{}' as clusterId,trunc(a.starttime) as startDate,b.* from stl_explain b , stl_query a where a.query=b.query and a.endtime > '{}'".format(clusterId,stlQueryLastProcessedTSValue),"stl_explain",job_configs)
functions.saveToS3(returnDF,s3Prefix,"stl_explain",["clusterid","startdate"],job_configs)

#### Query #####

stlQueryLastProcessedTSValue= functions.getLastProcessedTSValue(clusterId+"_stl_query",job_configs)
returnDF=functions.runQuery("select '{}' as clusterId,trunc(starttime) as startDate,* from stl_query where endtime > '{}'".format(clusterId,stlQueryLastProcessedTSValue),"stl_query",job_configs)
functions.saveToS3(returnDF,s3Prefix,"stl_query",["clusterid","startdate"],job_configs)
latestTimestampVal=functions.getMaxValue(returnDF,"endtime",job_configs)
functions.updateLastProcessedTSValue(clusterId+"_stl_query",latestTimestampVal[0],job_configs)

#### DDL Text #####

stlDDLTextProcessedTSValue = functions.getLastProcessedTSValue(clusterId+"_stl_ddltext",job_configs)
returnDF=functions.runQuery("select '{}' as clusterId,trunc(starttime) as startDate,* from stl_ddltext where endtime > '{}'".format(clusterId,stlDDLTextProcessedTSValue),"stl_ddltext",job_configs)
functions.saveToS3(returnDF,s3Prefix,"stl_ddltext",["clusterid","startdate"],job_configs)
latestTimestampVal=functions.getMaxValue(returnDF,"endtime",job_configs)
functions.updateLastProcessedTSValue(clusterId+"_stl_ddltext",latestTimestampVal[0],job_configs)

#### Utility Text #####

stlUtilityTextProcessedTSValue = functions.getLastProcessedTSValue(clusterId+"_stl_utilitytext",job_configs)
returnDF=functions.runQuery("select '{}' as clusterId,trunc(starttime) as startDate,* from stl_utilitytext where endtime > '{}'".format(clusterId,stlUtilityTextProcessedTSValue),"stl_utilitytext",job_configs)
functions.saveToS3(returnDF,s3Prefix,"stl_utilitytext",["clusterid","startdate"],job_configs)
latestTimestampVal=functions.getMaxValue(returnDF,"endtime",job_configs)
functions.updateLastProcessedTSValue(clusterId+"_stl_utilitytext",latestTimestampVal[0],job_configs)

#### Alert Event Log  #####

stlAlertEventLogProcessedTSValue = functions.getLastProcessedTSValue(clusterId+"_stl_alert_event_log",job_configs)
returnDF=functions.runQuery("select '{}' as clusterId,trunc(event_time) as startDate,* from stl_alert_event_log where event_time > '{}'".format(clusterId,stlAlertEventLogProcessedTSValue),"stl_alert_event_log",job_configs)
functions.saveToS3(returnDF,s3Prefix,"stl_alert_event_log",["clusterid","startdate"],job_configs)
latestTimestampVal=functions.getMaxValue(returnDF,"event_time",job_configs)
functions.updateLastProcessedTSValue(clusterId+"_stl_alert_event_log",latestTimestampVal[0],job_configs)


#### STL_SCAN #####

stlScanLastProcessedTSValue= functions.getLastProcessedTSValue(clusterId+"_stl_scan",job_configs)
returnDF=functions.runQuery("select '{}' as clusterId,trunc(starttime) as startDate,* from stl_scan where starttime > '{}'".format(clusterId,stlScanLastProcessedTSValue),"stl_scan",job_configs)
functions.saveToS3(returnDF,s3Prefix,"stl_scan",["clusterid","startdate"],job_configs)
latestTimestampVal=functions.getMaxValue(returnDF,"starttime",job_configs)
functions.updateLastProcessedTSValue(clusterId+"_stl_scan",latestTimestampVal[0],job_configs)

#### STL_WLM_QUERY #####

stlWLMQueryLastProcessedTSValue= functions.getLastProcessedTSValue(clusterId+"_stl_wlm_query",job_configs)
returnDF=functions.runQuery("select '{}' as clusterId,trunc(queue_start_time) as startDate,* from stl_wlm_query where queue_start_time > '{}'".format(clusterId,stlWLMQueryLastProcessedTSValue),"stl_wlm_query",job_configs)
functions.saveToS3(returnDF,s3Prefix,"stl_wlm_query",["clusterid","startdate"],job_configs)
latestTimestampVal=functions.getMaxValue(returnDF,"queue_start_time",job_configs)
functions.updateLastProcessedTSValue(clusterId+"_stl_wlm_query",latestTimestampVal[0],job_configs)


job.commit()
