from xml.etree.ElementTree import Element, SubElement, Comment, tostring
import boto3, os, time
from botocore.client import Config
import datetime

# the following environment variables are set - I'll put these as SAM variables in the future
podcast_name	= 'Streamripper'
podcast_author	= ''
podcast_desc	= 'Streamripper'
podcast_url		= 'https://tommcm-streamripper.s3.amazonaws.com/podcast.xml'
podcast_img 	= 'https://tommcm-streamripper.s3.amazonaws.com/podcast.jpg'
link_expiry 	= '604800'
s3_bucket		= os.environ['s3_bucket']

s3 = boto3.client("s3")

def get_matching_s3_objects(bucket, prefix="", suffix=""):
    """
    Generate objects in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch objects whose key starts with
        this prefix (optional).
    :param suffix: Only fetch objects whose keys end with
        this suffix (optional).
    """
    paginator = s3.get_paginator("list_objects_v2")
    kwargs = {'Bucket': bucket}

    # We can pass the prefix directly to the S3 API.  If the user has passed
    # a tuple or list of prefixes, we go through them one by one.
    if isinstance(prefix, str):
        prefixes = (prefix, )
    else:
        prefixes = prefix

    for key_prefix in prefixes:
        kwargs["Prefix"] = key_prefix

        for page in paginator.paginate(**kwargs):
            try:
                contents = page["Contents"]
            except KeyError:
                break

            for obj in contents:
                key = obj["Key"]
                if key.endswith(suffix):
                    yield obj

def get_matching_s3_keys(bucket, prefix="", suffix=""):
    """
    Generate the keys in an S3 bucket.

    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    for obj in get_matching_s3_objects(bucket, prefix, suffix):
        # yield obj["Key"]
        yield obj

# create the XML document root
def make_root():
    # add XML headers
    rss = Element('rss', version='2.0')
    rss.set('atom', 'http://www.w3.org/2005/Atom')
    rss.set('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')

    # add a channel containing the details of the podcast
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = podcast_name
    SubElement(channel, 'author').text = podcast_author
    SubElement(channel, 'description').text = podcast_desc
    SubElement(channel, 'link').text = podcast_url
    SubElement(channel, 'language').text = 'en-us'
    SubElement(channel, 'lastBuildDate').text = time.strftime("%a, %d %b %Y %H:%M:%S %Z")
    SubElement(channel, 'pubDate').text = time.strftime("%a, %d %b %Y %H:%M:%S %Z")

    # add a podcast image which the podcast client will display
    image = SubElement(channel, 'image')
    SubElement(image, 'url').text = podcast_img
    SubElement(image, 'title').text = podcast_desc
    SubElement(image, 'link').text = podcast_url

    for obj in get_matching_s3_keys(bucket=s3_bucket, prefix='', suffix='.mp3'):
        z = s3.generate_presigned_url('get_object', Params={'Bucket': s3_bucket, 'Key': obj['Key']},
                                          ExpiresIn=link_expiry)

        # use the folder name as the radiostationist name and the filename as the showname name
        radiostation, showname, episode = obj['Key'].split('/')
        print (radiostation, showname, episode)

        # obtain episode timestamp details from filename
        episode_details = episode.split('-')
        # print (episode_details)
        episode_year = episode_details[2]
        episode_month = episode_details[3]
        episode_date_time = episode_details[4]

        # TODO: fix file name in Streamripper so that it's easier to split.  'RADIOSTATION_SHOWNAME_YYYY-MM-DD-DAY-HH-MM'
        episode_date_time_details = episode_date_time.split('_')
        # print (episode_date_time_details)
        episode_date = episode_date_time_details[0]
        episode_day = episode_date_time_details[1]

        episode_created_date = datetime.datetime(int(episode_year), int(episode_month), int(episode_date))

        item = SubElement(channel, 'item')
        SubElement(item, 'description').text = str(radiostation) + ' - ' + showname.split('.')[
            0] + ' - ' + episode_created_date.strftime("%d %b %Y")
        SubElement(item, 'radiostationist').text = radiostation
        SubElement(item, 'title').text = str(radiostation) + ' - ' + showname.split('.')[
            0] + ' - ' + episode_created_date.strftime("%d %b %Y")
        SubElement(item, 'pubDate').text = episode_created_date.strftime("%a, %d %b %Y %H:%M:%S %Z")
        SubElement(item, 'size').text = str(obj['Size'])
        SubElement(item, 'enclosure', url=z, length=str(obj['Size']), type='audio/mpeg')
        SubElement(item, 'guid').text = obj['Key'].strip()

    # upload the rss.xml file to S3 - in the future, include "ACL = 'public-read'" as a flag to publish the XML file
    s3.put_object(Bucket=s3_bucket, Body=tostring(rss), Key='podcast.xml', ContentType='application/xml',
                  ACL='public-read')
    print('uploaded XML document of ' + str(
        len(tostring(rss))) + ' bytes to https://' + s3_bucket + '.s3.amazonaws.com/podcast.xml')

# lambda handler
def handler(event, context):
	make_root()
