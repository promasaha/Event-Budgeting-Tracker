# Used for two things:
#   1. ECS Fargate deployment, if you go that route instead of Lambda.
#   2. Building a Lambda *container image* instead of a zip package, which is
#      the easier path when you have binary deps like psycopg2.
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

# --- Alternative target for ECS Fargate (build with `--target ecs-image`) ---
FROM python:3.12-slim AS ecs-image

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
