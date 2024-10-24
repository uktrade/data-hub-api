#!/bin/bash
set -x
awslocal s3 mb s3://data-flow-bucket-development
# Multipart file uploads from Your Files in the browser require ETag to be
# exposed but by default it's not, so we add a CORS config to expose it
awslocal s3api put-bucket-cors --bucket data-flow-bucket-development --cors-configuration file:///etc/localstack/init/ready.d/s3-cors.json
set +x

echo "S3 Configured"