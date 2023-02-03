# Use Cases for Querying IAM data and reporting

### For the below examples, we will typically want to do 2 things:
1. Determine the query you need and export as an environment variable.  Suggest to run the query in Prisma Cloud console first.  
> Example:
```
export RQL= config from iam where grantedby.cloud.policy.name = 'AdministratorAccess'
```
2. Determine what fields you would like to filter on to narrow down your output.  You can fetch all the available fields with this simple command:
```
pc -o columns rql --query $RQL
```

## Examples

### Output only the Identities that are granted a specific policy
Reminder, export query as a variable and determine what fields you would like to filter on to narrow down your output.
```
export RQL_S3Full= config from iam where grantedby.cloud.policy.name = 'AmazonS3FullAccess'
pc -o columns rql --query $RQL_S3Full
```

Output results via JSON
```
pc -o json rql --query $RQL_S3Full | jq 'map(.sourceResourceName) | unique'
```
> Example Output:
```
[
  "AppUser1",
  "AppUser2",
  "i-022a31ebcde34fa20"
]
```

Output via columns
```
pc --columns sourceResourceName,grantedByCloudEntityType rql --query $RQL_S3Full  
```
> Example Output:
```
╒══════════════════════╤════════════════════════════╕
│ sourceResourceName   │ grantedByCloudEntityType   │
╞══════════════════════╪════════════════════════════╡
│ AppUser1             │ group                      │
├──────────────────────┼────────────────────────────┤
│ AppUser2             │ group                      │
├──────────────────────┼────────────────────────────┤
│ i-022a31ebcde34fa20  │ role                       │
╘══════════════════════╧════════════════════════════╛
```

