FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y curl build-essential autoconf bison libssl-dev libyaml-dev libreadline-dev zlib1g-dev libncurses-dev libffi-dev libgdbm-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sSL https://cache.ruby-lang.org/pub/ruby/3.3/ruby-3.3.0.tar.gz | tar -C /tmp -xzf - \
    && cd /tmp/ruby-3.3.0 && ./configure --prefix=/usr/local && make -j$(nproc) && make install \
    && rm -rf /tmp/ruby-3.3.0 \
    && ruby --version | grep -q "3\.3\.0"
WORKDIR /workspace
