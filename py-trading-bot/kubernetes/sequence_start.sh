kubectl apply -f py-trading-bot/kubernetes/configmap.yml
kubectl apply -f py-trading-bot/kubernetes/secret.yml
kubectl apply -f py-trading-bot/kubernetes/redis.yml
kubectl apply -f py-trading-bot/kubernetes/postgres.yml
sleep 40
kubectl apply -f py-trading-bot/kubernetes/django.yml
kubectl apply -f py-trading-bot/kubernetes/django_migrate.yml
kubectl apply -f py-trading-bot/kubernetes/celery.yml
