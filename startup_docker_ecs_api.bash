#!/bin/bash

# Build latest docker image
docker build -t rosrect_ecs_api . -f Dockerfile

# Stop docker containers
docker stop ecs_api_server
docker rm ecs_api_server

# Run latest docker image
# Start ECS API
docker run -it --env-file runtime.env \
--name=ecs_api_server \
-p 8000:8000 \
--volume="${HOME}/open_ecs_api_server/ecs.db:/root/.cognicept/ecs.db" \
rosrect_ecs_api /src/ecs_endpoint.py