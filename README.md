## [psedge.github.io/hiking](https://psedge.github.io/hiking)

I'm trying to walk a lot more this year, aiming to get fit and explore my new home; so this is a visualisation
of my progress.

### Setup

1. Make a Strava dev application at [https://www.strava.com/settings/api](https://www.strava.com/settings/api)
2. Create:
    * a DynamoDB table to persist refresh tokens
    * an S3 bucket with public read
    * a Lambda function from polys.py
    * a role with permissions for the above
3. Create a CloudWatch Events trigger to periodically run the function