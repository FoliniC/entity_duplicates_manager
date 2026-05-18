#!/bin/bash

docker run -it --rm \
  -v "$(pwd):/home/gemini/workspace" \
  -v "$HOME/.gemini:/home/gemini/.gemini" \
  -v "$HOME/docker/homeassistant/config:/home/gemini/ha_config" \
  -e GEMINI_API_KEY="AIzaSyDDq-9o9iC50U0JcBw_cA7DAJJT6B10-sY" \
  tgagor/gemini-cli \
  gemini "$@"

