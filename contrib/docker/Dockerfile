FROM alpine:3.8 as stage1
MAINTAINER "nzlosh@yahoo.com"

ENV ERRBOT_USER=errbot

COPY docker_build_installer /root
RUN sh /root/docker_build_installer stage1


FROM alpine:3.8
COPY docker_build_installer /root
RUN sh /root/docker_build_installer stage2
COPY --from=stage1 /opt/errbot /opt/errbot

ENTRYPOINT /bin/sh
