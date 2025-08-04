#!/bin/bash

PUID=${PUID:-99}
PGID=${PGID:-100}
UMASK=${UMASK:-002}

umask $UMASK

# Check if we're running as root and can modify users/groups
if [ "$(id -u)" = "0" ]; then
    # We're root, so we can modify users/groups
    if [ "$PUID" != "314" ] || [ "$PGID" != "314" ]; then
        # Only modify if the requested IDs are different from default
        if [ "$PGID" != "314" ]; then
            groupmod -o -g "$PGID" titlecardmaker 2>/dev/null || true
        fi
        if [ "$PUID" != "314" ]; then
            usermod -o -u "$PUID" titlecardmaker 2>/dev/null || true
        fi
    fi
    
    # Change ownership of directories
    chown -R titlecardmaker:titlecardmaker /tcm /config 2>/dev/null || true
    
    # Switch to titlecardmaker user and execute command
    exec runuser -u titlecardmaker -g titlecardmaker -- "$@"
else
    # We're not root, so just execute the command directly
    # This handles cases where the container is run with --user flag
    exec "$@"
fi
