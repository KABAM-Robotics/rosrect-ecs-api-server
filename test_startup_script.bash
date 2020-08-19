#!/bin/bash
# Clean up
clear

# Build latest docker image
docker build -t rosrect_ecs_api . -f Dockerfile

# Stop docker containers
docker stop ecs_api_server
docker rm ecs_api_server

# Run latest docker image
# Start ECS API
docker run -it --env-file runtime.env \
--name=ecs_api_server \
--net=host \
--volume="${HOME}/rosrect-ecs-api/ecs.db:/root/.cognicept/ecs.db" \
rosrect_ecs_api /ecs_api_server/ecs_endpoint.py