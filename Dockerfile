FROM python:3.8
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg
ENV PROJECT_DIR /usr/local/src/webapp
WORKDIR ${PROJECT_DIR}

# Copy the AWS credentials to use for copying from the root
COPY .credentials /root/.aws/credentials

#include the files
COPY . ${PROJECT_DIR}/

#install python dedpendencies
RUN pip install boto3 requests

ENTRYPOINT  ["python", "audiocomposer-local.py", "--body"]
CMD ["{}"]
