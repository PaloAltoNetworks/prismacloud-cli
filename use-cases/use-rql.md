
# RQL With Prisma Cloud CLI

The new --field parameter of the rql command can be used to parse a file with 
RQL queries. This file needs to be in yaml format as the example below:

```
- name: Find all permissions granted to Users
  query: config from iam where grantedby.cloud.entity.type = 'user'

- name: Find all permissions granted to Roles
  query: config from iam where grantedby.cloud.entity.type = 'role'

- name: IAM identities that can delete DynamoDB tables
  query: config from iam where action.name = 'dynamodb:DeleteTable'
```

Examples to use this:

`pc -o count rql --file ~/.prismacloud/my-important-queries.yaml`
`pc rql --file ~/.prismacloud/my-important-queries.yaml`

### Sample output

Command

`pc -o markdown rql --file ~/.prismacloud/my-important-queries.yaml `

RQL Query name: Find all permissions granted to Roles
RQL Query: config from iam where grantedby.cloud.entity.type = 'role'
| id                             | sourcePublic   | sourceCloudType   | sourceCloudAccount   | sourceCloudRegion   |
|:-------------------------------|:---------------|:------------------|:---------------------|:--------------------|
| 7984fc7e5041b7439272897da5c948 | False          | AWS               | Pedro AWS Account    | AWS Oregon          |
| 538adb5f6ccea83434be64b9e3b882 |                |                   |                      |                     |
| 2c47                           |                |                   |                      |                     |
| 3206a93cd56dc0d983f67a994a648a | False          | AWS               | Pedro AWS Account    | AWS Oregon          |
| 9a7e2f47f8a1d8851f37433312c1bc |                |                   |                      |                     |
| a3d5                           |                |                   |                      |                     |

RQL Query name: Find all permissions granted to Groups
RQL Query: config from iam where grantedby.cloud.entity.type = 'group'
| id                             | sourcePublic   | sourceCloudType   | sourceCloudAccount   | sourceCloudRegion   |
|:-------------------------------|:---------------|:------------------|:---------------------|:--------------------|
| 177bef83192f13a4e11f439fa8f7bb | False          | AWS               | pete-aws             | AWS Global          |
| dc50ce83185092er44re4431d3cad0 |                |                   |                      |                     |
| 19ce                           |                |                   |                      |                     |
| 177bef83192f13aer11f4erfa8f7bb | False          | AWS               | pete-aws             | AWS Global          |
| dc50ce831850928ddfeb9461d3cad0 |                |                   |                      |                     |
| 19ce                           |                |                   |                      |                     |

RQL Query name: Show all INACTIVE identities and their allowed actions over the last specified number of days
RQL Query: config from iam where action.lastaccess.days > 90


