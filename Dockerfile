# syntax=docker/dockerfile:1
FROM python:3.11-slim AS python-reqs

# Install uv and generate requirements file
# Install gcc for building python dependencies
COPY backend/pyproject.toml pyproject.toml
RUN pip3 install --no-cache-dir --upgrade uv; \
    uv pip compile pyproject.toml > requirements.txt && \
    apt-get update && \
    apt-get install -y gcc

# Install TCM dependencies
RUN --mount=type=cache,target=/root/.cache \
    pip3 install -r requirements.txt

# Set base image for running TCM
FROM python:3.11-slim AS final
LABEL maintainer="CollinHeist" \
      description="Automated Title Card creator for Plex, Emby, and Jellyfin"

# Copy python packages from python-reqs
COPY --from=python-reqs /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Set working directory, copy source into container
WORKDIR /maker
COPY . /maker

# Finalize setup
RUN \
    # Create user and group to run TCM
    set -eux && \
    groupadd -g 314 titlecardmaker && \
    useradd -u 314 -g 314 titlecardmaker && \
    # Install imagemagick, curl (for healthcheck), and Node.js
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl imagemagick libmagickcore-6.q16-6-extra \
        nodejs npm && \
    cp backend/modules/ref/policy.xml /etc/ImageMagick-6/policy.xml && \
    # Remove apt cache and setup files
    rm -rf pyproject.toml /tmp/* /var/tmp/* /var/lib/apt/lists/*

# Copy python packages from python-reqs
COPY --from=python-reqs \
    /usr/local/lib/python3.11/site-packages \
    /usr/local/lib/python3.11/site-packages

# Install and build frontend
WORKDIR /maker/front_next
RUN npm install && npm run build

# Return to main directory
WORKDIR /maker

# Expose TCM Port and Next.js Port
EXPOSE 4242 3000

# Script environment variables
ENV TCM_IS_DOCKER=TRUE \
    TZ=UTC \
    NEXT_PUBLIC_API_URL=http://localhost:4242

# Healthcheck command
# Add --start-interval=10s back in when merged in Docker v24/v25
HEALTHCHECK --interval=3m --timeout=10s --start-period=3m \
    CMD curl --fail http://0.0.0.0:4242/api/healthcheck || exit 1

# Create startup script
RUN echo '#!/bin/bash\n\
cd /maker/front_next && npm start & \
cd /maker/backend && python3 -u -m uvicorn server:app --host 0.0.0.0 --port 4242' > /maker/start-services.sh && \
chmod +x /maker/start-services.sh

# Entrypoint
CMD ["/maker/start-services.sh"]
ENTRYPOINT ["bash", "./start.sh"]
