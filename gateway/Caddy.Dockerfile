FROM caddy:2.10.2@sha256:c3d7ee5d2b11f9dc54f947f68a734c84e9c9666c92c88a7f30b9cba5da182adb
# Upstream grants the executable CAP_NET_BIND_SERVICE. Executing that file
# with ALL capabilities dropped produces EPERM. Port 8443 needs no capability.
RUN setcap -r /usr/bin/caddy
USER 10001:10001
