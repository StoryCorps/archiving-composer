# ARG FUNCTION_DIR="/function"

FROM python:buster as build-image

# Install aws-lambda-cpp build dependencies and ffmpeg
RUN apt-get update && \
  apt-get install -y \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev \
  ffmpeg

# Install the function's dependencies
RUN pip install \
    --target /function \
        awslambdaric \
        boto3 \
        requests  

#include the files
RUN mkdir -p /function
COPY audiocomposer-local.py /function
COPY credentials.json /function


FROM python:buster

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Set working directory to function root directory
WORKDIR /function

# Copy in the built dependencies
COPY --from=build-image /function /function

# include built ffmpeg
COPY --from=mwader/static-ffmpeg:5.0-1 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:5.0-1 /ffprobe /usr/local/bin/

RUN chmod 755 credentials.json

ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "audiocomposer-local.lambda_handler" ]