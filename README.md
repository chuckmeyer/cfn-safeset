# cfn-safeset
Scan CloudFormation ChangeSets for replacement actions on stateful resources

```
cfn-safeset -h
usage: cfn-safeset [-h] [-c CHANGESET] [-s STACKNAME] [-f STACKNAME]
                   [-r REGION] [-v] [-d] [-l]

CloudFormation ChangeSet safety check

optional arguments:
  -h, --help            show this help message and exit

Standard:
  -c CHANGESET, --changeset CHANGESET
                        The CloudFormation change set to be evaluated
  -s STACKNAME, --stack STACKNAME
                        The stack name associated with this change set
  -f STACKNAME, --file FILENAME
                        File containing a valid CloudFormation change set
  -r REGION, --region REGION
                        The region where this change set exists
  -v, --version         Version of cfn-safeset

Advanced / Debugging:
  -d, --debug           Enable debug logging
  -l, --list            List stateful resources
```