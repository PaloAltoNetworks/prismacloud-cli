#!/bin/bash

# Accept Support Message
mkdir ~/.prismacloud
touch ~/.prismacloud/.community_supported_accepted

# Leverage the default env variables as described in:
# https://docs.github.com/en/actions/reference/environment-variables#default-environment-variables
if [[ $GITHUB_ACTIONS != "true" ]]
then
  pc --config environment "$@"
  exit $?
fi
