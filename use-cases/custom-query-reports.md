# Use Cases for Querying IAM data and reporting

As of this writing there are various ways to output your data.  Run `pc --help` to see currently available options.
```
pc --help
Usage: pc [OPTIONS] COMMAND [ARGS]...

  Prisma Cloud CLI (version: 0.6.9)

Options:
  -v, --verbose                   Enables verbose mode
  -vv, --very_verbose             Enables very verbose mode
  --filter TEXT                   Add search filter
  -o, --output [text|csv|json|html|clipboard|markdown|columns]
  -c, --config TEXT               Select configuration file in
                                  ~/.prismacloud/[CONFIGURATION].json
  --columns TEXT                  Select columns for output
  --help                          Show this message and exit.
```
We will utilize several variations of the current options in the examples to provide different results.  Explore more on your own.

### For the below examples, we will typically want to do 2 things:
1. Determine the query you need and export as an environment variable.  Suggest to run and confirm a valid query in Prisma Cloud console first.  
```
export RQL="config from iam where grantedby.cloud.policy.name = 'AdministratorAccess'"
```
2. Determine what fields you would like to filter on to narrow down your output.  You can fetch all the available fields with this simple command:
```
pc -o columns rql --query $RQL
```

## Examples

### Output only the Identities that are granted a specific policy
Reminder, export query as a variable and determine what fields you would like to filter on to narrow down your output.
```
export RQL_S3Full="config from iam where grantedby.cloud.policy.name = 'AmazonS3FullAccess'"
pc -o columns rql --query $RQL_S3Full
```

To display results via JSON
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

To display results via columns
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


### Roles with permissions to assume:role* or passrole:* to any resource without a conditional
```
export RQL_AssumePassRole="config from iam where dest.cloud.type = 'AWS' and dest.cloud.resource.name = '*'and grantedby.cloud.policy.type != 'Resource-based Policy' and source.cloud.resource.name!='*' and action.name in ( 'sts:AssumeRole', 'iam:PassRole' )"
```
To display results via columns
```
pc --columns sourceResourceName,grantedByCloudEntityType,grantedByCloudPolicyType,grantedByCloudPolicyName rql --query $RQL_AssumePassRole
```
> Example Output:
```
╒═══════════════════════════╤════════════════════════════╤════════════════════════════╤════════════════════════════╕
│ sourceResourceName        │ grantedByCloudPolicyName   │ grantedByCloudPolicyType   │ grantedByCloudEntityType   │
╞═══════════════════════════╪════════════════════════════╪════════════════════════════╪════════════════════════════╡
│ AppUser1                  │ AdministratorAccess        │ AWS Managed Policy         │ group                      │
├───────────────────────────┼────────────────────────────┼────────────────────────────┼────────────────────────────┤
│ DevOpsUser3               │ PowerUserAccess            │ AWS Managed Policy         │ role                       │
├───────────────────────────┼────────────────────────────┼────────────────────────────┼────────────────────────────┤
│ privesc-sre-user          │ privesc-sre-admin-policy   │ Customer Managed Policy    │ role                       │
├───────────────────────────┼────────────────────────────┼────────────────────────────┼────────────────────────────┤
│ application12345          │ LambdaExecutionRolePolicy  │ Inline Policy              │ role                       │
├───────────────────────────┼────────────────────────────┼────────────────────────────┼────────────────────────────┤
│ TheBoss                   │ AdministratorAccess        │ AWS Managed Policy         │ user                       │
╘═══════════════════════════╧════════════════════════════╧════════════════════════════╧════════════════════════════╛
```
To display same results via html and save to a file
```
pc -o html --columns sourceResourceName,grantedByCloudEntityType,grantedByCloudPolicyType,grantedByCloudPolicyName rql --query $RQL_AssumePassRole > file.html
```
To display same results to your clipboard
```
pc -o clipboard --columns sourceResourceName,grantedByCloudEntityType,grantedByCloudPolicyType,grantedByCloudPolicyName rql --query $RQL_AssumePassRole
```
- After above command executes, you can open up a spreadsheet tool like MS Excel or Google Sheets and simply paste the results.


### List Identities that can delete S3 buckets and if they used this permission in the last 90 days

```
export RQL_DeleteBucket="config from iam where dest.cloud.service.name = 's3' AND action.name = 's3:deletebucket' AND action.lastaccess.days > 90 "
```
```
pc --columns sourceResourceName,lastAccessStatus,lastAccessDate rql --query $RQL_DeleteBucket
```
> Example Output:
```
╒═══════════════════════════╤══════════════════╤═══════════════════════════╕
│ sourceResourceName        │ lastAccessDate   │ lastAccessStatus          │
╞═══════════════════════════╪══════════════════╪═══════════════════════════╡
│ AppUser1                  │                  │ NOT_ACCESSED_IN_TRACKING_ │
│                           │                  │ PERIOD                    │
├───────────────────────────┼──────────────────┼───────────────────────────┤
│ DevOpsUser3               │ 2023-01-25       │ ACCESSED                  │
├───────────────────────────┼──────────────────┼───────────────────────────┤
│ TheBoss                   │                  │ NOT_ACCESSED_IN_TRACKING_ │
│                           │                  │ PERIOD                    │
╘═══════════════════════════╧══════════════════╧═══════════════════════════╛
```


### List Azure Service Principals granted Owner Role and what level they were granted by

```
export RQL_AZ_OWNER_SPs="config from iam where dest.cloud.type = 'AZURE' AND grantedby.cloud.policy.type = 'Built-in Role' AND grantedby.cloud.policy.name = 'Owner' AND grantedby.cloud.type = 'AZURE' AND grantedby.cloud.entity.type = 'Service Principal' "
```
```
pc --columns sourceResourceName,grantedByCloudEntityType,sourceCloudAccount,grantedByLevelType,grantedByLevelName rql --query $RQL_AZ_OWNER_SPs
```
> Example Output:
```
╒═══════════════════════════╤═══════════════════════════╤════════════════════════════╤════════════════════════╤═══════════════════════════|
│ sourceCloudAccount        │ sourceResourceName        │ grantedByCloudEntityType   │ grantedByLevelType     │ grantedByLevelId          │ 
╞═══════════════════════════╪═══════════════════════════╪════════════════════════════╪════════════════════════╪═══════════════════════════╡
│ Azure QA                  │ ombarFuntionApp           │ Service Principal          │ Azure Subscription     │ /subscriptions/REDACTED-  │
│                           │                           │                            │                        │ -XXXXXXXXXXXXXX           │
│                           │                           │                            │                        │                           │
├───────────────────────────┼───────────────────────────┼────────────────────────────┼────────────────────────┼───────────────────────────|
│ Azure QA                  │ AzureResourceDeletionApp  │ Service Principal          │ Azure Subscription     │ /subscriptions/REDACTED-  │
│                           │                           │                            │                        │ -XXXXXXXXXXXXXX           │
│                           │                           │                            │                        │                           │
├───────────────────────────┼───────────────────────────┼────────────────────────────┼────────────────────────┼───────────────────────────|
│ Azure QA_Static_7         │ AzureResourceDeletionApp  │ Service Principal          │ Azure Resource         │ /subscriptions/REDACTED-  │
│                           │                           │                            │                        │ -XXXXXXXXXXXXXXX/resource │
│                           │                           │                            │                        │ Groups/TESTQA-AUTOMATION/ │ 
│                           │                           │                            │                        │ providers/Microsoft.DataL │
│                           │                           │                            │                        │ akeAnalytics/accounts/sta │
│                           │                           │                            │                        │ ticdla                    │
├───────────────────────────┼───────────────────────────┼────────────────────────────┼────────────────────────┼───────────────────────────|
│ Azure QA Tenant           │ Tenant onboard            │ Service Principal          │ Azure Management Group │ /providers/Microsoft.Mana │
│                           │                           │                            │                        │ gement/managementGroups/f │
│                           │                           │                            │                        │ REDACTED-XXXXXXXXXXXXX-   │
│                           │                           │                            │                        │ YYYYYYYYYYYY              │
├───────────────────────────┼───────────────────────────┼────────────────────────────┼────────────────────────┼───────────────────────────|
```

### List Azure Identities granted either Key Vault Administrator or Key Vault Reader Role and have unrestricted destination access
This would show all identities with these High risk roles that are not scoped to specific Key Vaults and could pose a data risk.

```
export RQL_AZ_KV="config from iam where dest.cloud.type = 'AZURE' AND grantedby.cloud.policy.type = 'Built-in Role' AND grantedby.cloud.policy.name IN ('Key Vault Reader', 'Key Vault Administrator') AND dest.cloud.service.name = 'Microsoft.KeyVault' AND dest.cloud.resource.name = '*' "
```
```
 pc --columns sourceResourceName,grantedByCloudEntityType,grantedByCloudPolicyName,destResourceName  rql --query $RQL_AZ_KV
```
> Example Output:
```
╒═════════════════════════╤════════════════════╤════════════════════════════╤════════════════════════════╕
│ sourceResourceName      │ destResourceName   │ grantedByCloudPolicyName   │ grantedByCloudEntityType   │
╞═════════════════════════╪════════════════════╪════════════════════════════╪════════════════════════════╡
│ abcdef-app-registration │ *                  │ Key Vault Reader           │ Service Principal          │
├─────────────────────────┼────────────────────┼────────────────────────────┼────────────────────────────┤
│ Shreyas                 │ *                  │ Key Vault Administrator    │ user                       │
╘═════════════════════════╧════════════════════╧════════════════════════════╧════════════════════════════╛
```


### Find all identities that can delete MS SQL DBs
```
export RQL_AZ_SQL_DELETE="config from iam where dest.cloud.type = 'AZURE' AND dest.cloud.resource.name = 'Microsoft.Sql' AND dest.cloud.resource.type = 'servers' AND action.name = 'Microsoft.Sql/servers/delete'"
```
To display results via columns
```
pc --columns sourceResourceName,grantedByCloudEntityType,grantedByCloudPolicyName,destResourceName  rql --query $RQL_AZ_SQL_DELETE
```
> Example Output:
```
╒═══════════════════════════╤════════════════════╤════════════════════════════╤════════════════════════════╕
│ sourceResourceName        │ destResourceName   │ grantedByCloudPolicyName   │ grantedByCloudEntityType   │
╞═══════════════════════════╪════════════════════╪════════════════════════════╪════════════════════════════╡
│ Prath                     │ *                  │ Owner                      │ group                      │
├───────────────────────────┼────────────────────┼────────────────────────────┼────────────────────────────┤
│ Varad                     │ *                  │ Owner                      │ user                       │
├───────────────────────────┼────────────────────┼────────────────────────────┼────────────────────────────┤
│ Varad                     │ *                  │ Contributor                │ group                      │
├───────────────────────────┼────────────────────┼────────────────────────────┼────────────────────────────┤
│ cohen                     │ *                  │ Contributor                │ user                       │
├───────────────────────────┼────────────────────┼────────────────────────────┼────────────────────────────┤
│ Eli                       │ *                  │ Contributor                │ user                       │
├───────────────────────────┼────────────────────┼────────────────────────────┼────────────────────────────┤
│ azureautomationaccount01_ │ *                  │ Contributor                │ Service Principal          │
│ REDACTED=                 │                    │                            │                            │
├───────────────────────────┼────────────────────┼────────────────────────────┼────────────────────────────┤
```
To display same results via html and save to a file
```
pc -o html --columns sourceResourceName,grantedByCloudEntityType,grantedByCloudPolicyName,destResourceName  rql --query $RQL_AZ_SQL_DELETE > file.html
```
To display same results to your clipboard
```
pc -o clipboard --columns sourceResourceName,grantedByCloudEntityType,grantedByCloudPolicyName,destResourceName  rql --query $RQL_AZ_SQL_DELETE
```
- After above command executes, you can open up a spreadsheet tool like MS Excel or Google Sheets and simply paste the results.
