#!/bin/sh
# روی هاست (نه داخل کانتینر) اجرا می‌شه — با کرون، مثلاً روزی یک بار:
#   0 3 * * * /path/to/RoyaEvent/infra/renew-certs.sh >> /var/log/royaevent-renew.log 2>&1
#
# certbot renew خودش no-op می‌مونه اگه هنوز به ~۳۰ روز مانده به انقضا نرسیده
# باشه؛ nginx فقط وقتی reload می‌شه که واقعاً گواهی جدیدی صادر شده باشه.
set -eu
cd "$(dirname "$0")"

docker compose -f docker-compose.prod.yml run --rm certbot renew --webroot -w /var/www/certbot --quiet \
  && docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
