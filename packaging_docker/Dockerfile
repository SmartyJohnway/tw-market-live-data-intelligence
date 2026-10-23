ARG BASE_IMAGE=python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741
FROM ${BASE_IMAGE} AS dependencies

COPY requirements-linux-amd64-cp313.txt /tmp/requirements.txt
COPY dependency-lock-linux-amd64-cp313.json /tmp/dependency-lock.json
COPY wheelhouse/ /tmp/wheelhouse/
RUN python -m venv /opt/tw-market/venv \
    && /opt/tw-market/venv/bin/python -m pip install \
       --disable-pip-version-check --no-cache-dir --no-compile --no-index \
       --find-links=/tmp/wheelhouse --only-binary=:all: --require-hashes \
       -r /tmp/requirements.txt \
    && /opt/tw-market/venv/bin/python -m pip check

ARG BASE_IMAGE=python:3.13-alpine@sha256:bf12ecc0bea3f171d55145dd02c78b5eeb09f30ee2ac9cc2b4c9e4e8f5e30741
FROM ${BASE_IMAGE} AS runtime
ARG SOURCE_TREE
ARG DEPENDENCY_LOCK_SHA256
LABEL org.opencontainers.image.title="TW-Market Local Service" \
      org.opencontainers.image.source="https://github.com/SmartyJohnway/tw-market-live-data-intelligence" \
      org.twmarket.source-tree="${SOURCE_TREE}" \
      org.twmarket.dependency-lock-sha256="${DEPENDENCY_LOCK_SHA256}"

RUN addgroup -S -g 10001 twmarket \
    && adduser -S -D -H -u 10001 -G twmarket twmarket \
    && mkdir -p /opt/tw-market/app /var/lib/tw-market/home /var/lib/tw-market/state \
    && chown -R 10001:10001 /var/lib/tw-market
COPY --from=dependencies /opt/tw-market/venv /opt/tw-market/venv
COPY app/ /opt/tw-market/app/
RUN chmod -R a-w /opt/tw-market/app /opt/tw-market/venv

ENV PATH="/opt/tw-market/venv/bin:${PATH}" \
    PYTHONPATH="/opt/tw-market/app" \
    PYTHONDONTWRITEBYTECODE="1" \
    PYTHONUNBUFFERED="1" \
    PIP_NO_CACHE_DIR="1" \
    TW_MARKET_HOME="/var/lib/tw-market/home" \
    TW_MARKET_STATE_ROOT="/var/lib/tw-market/state"
WORKDIR /opt/tw-market/app
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["python", "-m", "scripts.tw_market_docker"]
CMD ["serve"]
