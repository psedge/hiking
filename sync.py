import os
import json
from datetime import datetime

import boto3
import http.client

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']


def lambda_handler(event, context) -> dict:
    """
    Handle cron invocation
    :param event:
    :param context:
    :return:
    """
    # Try to fetch the last refresh token from dynamo
    res = dynamodb.get_item(TableName='strava', Key={'id': {"N": "1"}})
    refresh_token = res['Item']['token']['S']
    try:
        access_token, refresh_token = refresh(refresh_token)
    except Exception as e:
        return {'status': 500, 'message': "Invalid refresh token? " + str(e)}
    res = dynamodb.put_item(TableName='strava', Item={'id': {'N': '1'}, 'token': {'S': refresh_token}})

    if access_token is None:
        # Grab an auth code from
        # https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,activity:read_all
        auth_code = ""
        res = requests.post("https://www.strava.com/api/v3/oauth/token", data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'authorization_code',
            'code': auth_code
        }, headers={'X-Content-Type': 'application/json'})
        body = json.loads(res.content.decode("utf-8"))
        refresh_token = body['refresh_token']
        return {'status': 202, 'message': "put this refresh token in dynamo:" + refresh_token}

    # Fetch your activities & build data
    try:
        body = get_activities(access_token)
    except Exception as e:
        return {'status': 500, 'message': "Failed to fetch your shit bro: " + str(e)}

    years = {str(i): {
        'distance': 0,
        'months': {n: 0 for n in range(1, 13)},
        'lines': [],
    } for i in range(2018, 2025)}

    for activity in body:
        if activity['type'] == 'Hike':
            year = activity['start_date'][0:4]

            years[year]['distance'] += round(activity['distance'], 2)
            years[year]['months'][int(activity['start_date'][5:7])] = round(activity['distance'] / 1000 + years[year]['months'][int(activity['start_date'][5:7])], 2)
            years[year]['lines'].append(activity['map']['summary_polyline'])

    total_distance = sum([year_body['distance'] for year_body in years.values()])/1000
    filtered_years = {year: years[year] for year in years if (years[year]['distance'] != 0 or year == str(datetime.now().year))}
    body = "data =" + json.dumps(filtered_years)

    response = s3.put_object(
        Bucket='psedge-strava',
        Key='data-2.js',
        Body=body,
        ACL='public-read'
    )

    return {
        'status': 200,
        'message': f"Total Distance: {total_distance}m / {total_distance / 1000}km"
    }


def refresh(refresh_token) -> (str, str):
    """
    Exchange the refresh token for an access token
    :param refresh_token:
    :return:
    """
    conn = http.client.HTTPSConnection("www.strava.com")
    conn.request("POST", "/oauth/token", json.dumps({
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }), headers={'Content-Type': 'application/json'})

    res = conn.getresponse()
    body = res.read()
    if res.status != 200:
        raise Exception(body)
    contents = json.loads(body.decode("utf-8"))

    return contents['access_token'], contents['refresh_token']


def get_activities(access_token) -> list:
    """
    List the activities for this athlete
    :param access_token:
    :return:
    """
    contents = {}

    page = 1
    page_results = 1
    while page_results > 0:
        conn = http.client.HTTPSConnection("www.strava.com")
        conn.request("GET", f"/api/v3/athlete/activities?per_page=100&page={page}", headers={
            'Authorization': 'Bearer ' + access_token
        })
        res = conn.getresponse()
        body = res.read()
        if res.status != 200:
            raise Exception(body)

        page_content = json.loads(body.decode("utf-8"))
        contents = contents + page_content
        page_results = len(page_content)
        page += 1

    return contents
