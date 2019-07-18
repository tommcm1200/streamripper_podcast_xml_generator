

sam package --template-file sam.yaml --s3-bucket tommcm-streamripper --output-template-file packaged.yaml

aws cloudformation deploy --template-file /Users/tommcm/Git/streamripper_podcast_xml_generator/packaged.yaml --stack-name streamripper-podcast-generator --parameter-overrides  ParameterKey=MusicBucket,ParameterValue=tommcm-streamripper


