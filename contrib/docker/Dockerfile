FROM alpine:3.8 as stage1
MAINTAINER "nzlosh@yahoo.com"

ENV ERRBOT_USER=errbot

COPY docker_build_installer /root
RUN sh /root/docker_build_installer stage1


FROM alpine:3.8
COPY docker_build_installer /root
RUN sh /root/docker_build_installer stage2
COPY --from=stage1 /opt/errbot /opt/errbot
COPY gitter_config.py /opt/errbot
COPY mattermost_config.py /opt/errbot
COPY rocketchat_config.py /opt/errbot
COPY slack_config.py /opt/errbot
COPY discord_config.py /opt/errbot

# Export plugins as a volume so host can read plugin static web content from err-stackstorm.
VOLUME "/opt/errbot/plugins"

ENTRYPOINT /bin/sh
