# Builds a Lambda *container image* (rather than a zip package), which is
# the easier path when you have binary deps like psycopg2.
#
# For local development, prefer running `uvicorn app.main:app --reload`
# directly (faster iteration) against the docker-compose Postgres — this
# Dockerfile is for deployment, not local dev.

FROM public.ecr.aws/lambda/python:3.12 AS lambda-image

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY app ${LAMBDA_TASK_ROOT}/app
COPY alembic ${LAMBDA_TASK_ROOT}/alembic
COPY alembic.ini ${LAMBDA_TASK_ROOT}/

CMD ["app.main.handler"]
