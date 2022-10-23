# Introduction
You can operate the bot in Docker and Kubernetes. Instruction were tested with Linux, but should be translatable for other operating systems.

1. Clone the project
2. Start minikube or equivalent, and link it to Docker. In your terminal:

    start minikube
    
3. Link docker to minikube  
    
    eval $(minikube docker-env) 
    
4. At the root create the Docker image. Introduce your Github token to be able to download vectorbtpro with https. If you use ssh, adapt the line corresponding to this download in the Dockerfile.
```
docker build . -t py-trading-bot --build-arg GH_TOKEN=<you Github Token>
```
5. Change the password. Go in py-trading-bot/secret.yml and replace the items, especially the token for Telegram, with your values coded in base64, as it is the standard for secrets in Kubernetes.
6. Run py-trading-bot/kubernetes/sequence_start.sh It is just some kubectl command in a sequence, you can also run them manually.
7. Check that everything went well. All pods should be running.
```
kubectl get pods
```
8. Expose the service 
```
minikube service py-trading-bot-service --url
```
and click on the link to access the bot.

9. Start the background scheduler, including Telegram, by clicking on "start bot". Your telegram should display you "I'm back online".

Alternatively you can also start jupyter with:
```
docker run --rm -p 8888:8888 -v "$PWD":/home/jovyan/work py-trading-bot
```

If you want to read the logs of the bot:
```
kubectl logs <name of the worker pod>
``
