VM deployment support files for `simPro`.

Usage on the VM:

1. Copy the repo to `/opt/simPro`.
2. Run `bash /opt/simPro/deploy/vm_install.sh`.

This installs Python and Nginx, creates a virtualenv, runs `gunicorn` as a
`systemd` service on `127.0.0.1:8080`, and exposes the app on port `80`.
