#!/bin/bash
set -x
awslocal s3 mb s3://data-flow-bucket-local
awslocal s3 mb s3://data-hub-documents-local
# Multipart file uploads from Your Files in the browser require ETag to be
# exposed but by default it's not, so we add a CORS config to expose it
awslocal s3api put-bucket-cors --bucket data-flow-bucket-local --cors-configuration file:///etc/localstack/init/ready.d/s3-cors.json
awslocal s3api put-bucket-cors --bucket data-hub-documents-local --cors-configuration file:///etc/localstack/init/ready.d/s3-cors.json
set +x

echo "S3 Configured"