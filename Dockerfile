FROM python:3.8

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

RUN pip install pipenv

ENV PROJECT_DIR /usr/local/src/webapp

WORKDIR ${PROJECT_DIR}

COPY Pipfile Pipfile.lock ${PROJECT_DIR}/

COPY . ${PROJECT_DIR}/

RUN pipenv install --system --deploy

# CMD [ "bash" ]
ENTRYPOINT ["python", "audiocomposer-local.py", "--body=$BODY",]
