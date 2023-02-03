## Use Cases for Querying IAM data and reporting

Output only the Identities that are granted a specific policy
1. Determine the query you need and export as an environment variable
```
export RQL_S3Full= config from iam where grantedby.cloud.policy.name = 'AmazonS3FullAccess'
```
2. Determine what fields you would like to filter on to narrow down your output:
```
pc -o columns rql --query $RQL_S3Full
```

Example to output results via JSON
```
pc -o json rql --query $RQL_S3Full | jq 'map(.sourceResourceName) | unique'
```

Example to output via columns
```
pc --columns sourceResourceName,grantedByCloudEntityType rql --query $RQL_S3Full  
```
