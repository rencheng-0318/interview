ARG POSTGRES_IMAGE=mirror.gcr.io/library/postgres:18-alpine@sha256:9a8afca54e7861fd90fab5fdf4c42477a6b1cb7d293595148e674e0a3181de15

FROM ${POSTGRES_IMAGE} AS pgvector-builder

ADD https://github.com/pgvector/pgvector.git#159b79aaad5983fb7459c1e3df2897fbb2d11788 /tmp/pgvector

RUN apk add --no-cache build-base clang21 llvm21-dev \
    && make -C /tmp/pgvector OPTFLAGS="" \
    && make -C /tmp/pgvector install

FROM ${POSTGRES_IMAGE}

COPY --from=pgvector-builder /usr/local/lib/postgresql/vector.so /usr/local/lib/postgresql/vector.so
COPY --from=pgvector-builder /usr/local/lib/postgresql/bitcode/vector /usr/local/lib/postgresql/bitcode/vector
COPY --from=pgvector-builder /usr/local/lib/postgresql/bitcode/vector.index.bc /usr/local/lib/postgresql/bitcode/vector.index.bc
COPY --from=pgvector-builder /usr/local/share/postgresql/extension/vector* /usr/local/share/postgresql/extension/
