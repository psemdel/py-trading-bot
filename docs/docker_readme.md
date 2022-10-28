# First time
You can operate the bot in Docker and Kubernetes. Instruction were tested with Linux, but should be translatable for other operating systems.

1. Clone the project
2. Start minikube or equivalent. In your terminal:

    start minikube
    
3. Link docker to minikube:  
    
    eval $(minikube docker-env) 
    
4. At the root create the Docker image. Introduce your Github token to be able to download vectorbtpro with https. If you use ssh, adapt the line corresponding to this download in the Dockerfile.

    docker build . -t py-trading-bot --build-arg GH_TOKEN=<you Github Token>

5. Change the password. Go in py-trading-bot/secret.yml and replace the items, especially the token for Telegram, with your values coded in base64, as it is the standard for secrets in Kubernetes.
6. Run 

    py-trading-bot/kubernetes/sequence_start_first_time.sh 
    
It is just some kubectl command in a sequence, you can also run them manually.

7. Check that everything went well. All pods should be running.

    kubectl get pods

8. Expose the service 


    minikube service py-trading-bot-service --url

and click on the link to access the bot.

9. Start the background scheduler, including Telegram, by clicking on "start bot". Your telegram should display you "I'm back online".

Alternatively you can also start jupyter with:

    docker run --rm -p 8888:8888 -v "$PWD":/home/jovyan/work py-trading-bot

If you want to read the logs of the bot:

    kubectl logs <name of the worker pod>

#Troubleshooting 
If for any reason the sequence_start_first_time.sh lead to an error, you need to clean properly Kubernetes before repeating the step. It means obviously removing the deployments with

    kubectl delete deployment <name of the deployment>
    
The jobs:

    kubectl delete job <name of the job>
    
And also the permanent volumes (it will kill your DB, use it only the very first time you install):

    kubectl delete pvc py-trading-bot-postgres-pvc
    kubectl delete pv py-trading-bot-postgres-pv
    
## Error auth_user_username_key
In the logs of py-trading-bot pod (kubectl logs <name of py-trading-bot>) you find:

    UniqueViolation: duplicate key value violates unique constraint "auth_user_username_key" 
    
Then remove in kubernetes/django_migrate.yml the line which create the superuser

    echo "from django.contrib.auth.models import User; User.objects.create_superuser('$DJANGO_SUPERUSER', 'admin@example.com', '$DJANGO_PASSWORD')" | python manage.py shell;

# Next time
When you want to restart your bot later, the process is lighter as the docker images are already loaded and so on.

1. Start minikube or equivalent. In your terminal:

    start minikube
    
2. Link docker to minikube:      
   
    eval $(minikube docker-env)   
    
3. Run 

    py-trading-bot/kubernetes/sequence_start.sh     
    
4. Expose the service 


    minikube service py-trading-bot-service --url

and click on the link to access the bot.

5. Start the background scheduler, including Telegram, by clicking on "start bot". Your telegram should display you "I'm back online".




