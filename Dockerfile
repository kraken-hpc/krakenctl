### -*- Mode: Dockerfile; fill-column: 80; comment-auto-fill-only-coetments: t; tab-width: 4 -*-
################################################################################
# Dockerfile: container definitions for krakenctl ephemeral container
#             this helps with running krakenctl and not having to setup a sepcial
#             python3 environment
# 
# Author: J. Lowell Wofford <lowell@lanl.gov>
# 
# This software is open source software available under the BSD-3 license.
# Copyright (c) 2021, Triad National Security, LLC
# See LICENSE file for details.
# 
### Instructions
# 0) Setup podman & buildah (or docker).
# 1) to build
#    $ git clone git@github.com:kraken-hpc/krakenctl.git
#    $ cd krakenctl
#    $ buildah bud -t krakenctl
# 2) to use
#    $ alias krakenctl="podman run --rm -it krakenctl"
#    $ krakenctl -h
################################################################################

### Build Arguments (override via "--build-arg")
ARG PYVER="3.8.8"

FROM docker.io/library/python:${PYVER}-alpine
LABEL maintainer="J. Lowell Wofford <lowell@lanl.gov>"

WORKDIR "/krakenctl"
COPY . .

# install python deps
RUN pip3 install pyyaml requests rich

ENTRYPOINT [ "/krakenctl/krakenctl.py" ]
CMD [ "-h" ]
