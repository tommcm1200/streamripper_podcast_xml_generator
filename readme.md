# Overview
This template is a podcast XML generator for the Streamripper episodes.

##Pre-reqs
Create s3 bucket which episodes will be stored.

##Deployment
`sam package --template-file sam.yaml --s3-bucket [BUCKETNAME] --output-template-file packaged.yaml`

`aws cloudformation deploy --template-file packaged.yaml --stack-name [STACKNAME] --parameter-overrides  MusicBucket=[BUCKETNAME]--capabilities CAPABILITY_IAM`


