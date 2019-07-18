#!/usr/bin/python
# marek kuczynski, @marekq
# www.marek.rocks
# source; https://github.com/marekq/lambda-podcast

from xml.etree.ElementTree import Element, SubElement, Comment, tostring 
import boto3, os, time
import datetime

# the following environment variables are set - I'll put these as SAM variables in the future
podcast_name	= 'Streamripper'		
podcast_author	= ''				
podcast_desc	= 'Streamripper'	
podcast_url		= 'https://tommcm-streamripper.s3.amazonaws.com/podcast.xml'
podcast_img 	= 'https://tommcm-streamripper.s3.amazonaws.com/podcast.jpg'
link_expiry 	= '604800'					
s3_bucket		= os.environ['s3_bucket']

# create the XML document root
def make_root():
	# add XML headers 
	rss 		= Element('rss', version = '2.0')
	rss.set('atom', 'http://www.w3.org/2005/Atom')
	rss.set('itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')

	# add a channel containing the details of the podcast
	channel 	= SubElement(rss, 'channel')
	SubElement(channel, 'title').text = podcast_name
	SubElement(channel, 'author').text = podcast_author
	SubElement(channel, 'description').text = podcast_desc
	SubElement(channel, 'link').text = podcast_url
	SubElement(channel, 'language').text = 'en-us'
	SubElement(channel, 'lastBuildDate').text = time.strftime("%a, %d %b %Y %H:%M:%S %Z")
	SubElement(channel, 'pubDate').text = time.strftime("%a, %d %b %Y %H:%M:%S %Z")

	# add a podcast image which the podcast client will display
	image		= SubElement(channel, 'image')
	SubElement(image, 'url').text = podcast_img
	SubElement(image, 'title').text = podcast_desc
	SubElement(image, 'link').text = podcast_url

	# create session to s3 music bucket
	s	= boto3.client('s3')
	a	= s.list_objects_v2(Bucket = s3_bucket)

	# check all mp3 files in the bucket
	for x in a['Contents']:
		if 'mp3' in x['Key'] and  '/' in x['Key']:

			# create presigned URL for the MP3
			z 			= s.generate_presigned_url('get_object', Params = {'Bucket': s3_bucket, 'Key': x['Key']}, ExpiresIn = link_expiry)
			
			# use the folder name as the radiostationist name and the filename as the showname name
			radiostation, showname, episode 	= x['Key'].split('/')
			
			# obtain episode timestamp details from filename
			episode_details = episode.split('-')
			# print (episode_details)
			episode_year = episode_details[2]
			episode_month = episode_details[3]
			episode_date_time = episode_details[4]
			
			#TODO: fix file name in Streamripper so that it's easier to split.  'RADIOSTATION_SHOWNAME_YYYY-MM-DD-DAY-HH-MM'
			episode_date_time_details = episode_date_time.split('_')
			# print (episode_date_time_details)
			episode_date = episode_date_time_details[0]
			episode_day = episode_date_time_details[1]
			
			# episode_created_date = "{}-{}-{} 00:00:00+00:00".format(episode_year,episode_month,episode_date)
			episode_created_date = datetime.datetime(int(episode_year), int(episode_month), int(episode_date))

			
			item		= SubElement(channel, 'item')
			SubElement(item, 'description').text = str(radiostation)+' - '+showname.split('.')[0]+' - '+episode_created_date.strftime("%d %b %Y")
			# SubElement(item, 'description').text = str(radiostation)+' - '+showname.split('.')[0]+' - '+x['LastModified'].strftime("%d %b %Y")
			SubElement(item, 'radiostationist').text = radiostation
			SubElement(item, 'title').text = str(radiostation)+' - '+showname.split('.')[0]+' - '+episode_created_date.strftime("%d %b %Y")
			# SubElement(item, 'title').text = str(radiostation)+' - '+showname.split('.')[0]+' - '+x['LastModified'].strftime("%d %b %Y")
			SubElement(item, 'pubDate').text = episode_created_date.strftime("%a, %d %b %Y %H:%M:%S %Z")
			# SubElement(item, 'pubDate').text = x['LastModified'].strftime("%a, %d %b %Y %H:%M:%S %Z")
			SubElement(item, 'size').text = str(x['Size'])
			SubElement(item, 'enclosure', url = z, length = str(x['Size']), type = 'audio/mpeg')
			SubElement(item, 'guid').text = x['Key'].strip()

	# upload the rss.xml file to S3 - in the future, include "ACL = 'public-read'" as a flag to publish the XML file
	s.put_object(Bucket = s3_bucket, Body = tostring(rss), Key = 'podcast.xml', ContentType = 'application/xml', ACL = 'public-read')
	print('uploaded XML document of '+str(len(tostring(rss)))+' bytes to https://'+s3_bucket+'.s3.amazonaws.com/podcast.xml')

# lambda handler
def handler(event, context):
	make_root()