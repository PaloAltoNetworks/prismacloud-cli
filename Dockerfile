FROM python:3.10-alpine

ENV RUN_IN_DOCKER=True

# Metadata as described above
LABEL maintainer="Simon Melotte <smelotte@paloaltonetworks.com>" \
      description="Docker image for prismacloud-cli"

RUN apk --no-cache add build-base git curl jq bash
RUN pip3 install --no-cache-dir -U prismacloud-cli

# Copy your entrypoint script
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Default command when container runs
ENTRYPOINT ["/entrypoint.sh"]