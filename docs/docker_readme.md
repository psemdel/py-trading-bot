# First time
You can operate the bot in Docker and Kubernetes. Instruction were tested with Linux, but should be translatable for other operating systems.

1. Clone the project. Optionally, you can get rid of the folder saved_cours, which is not needed in production.
2. Adapt the Configuration in trading_bot/settings see the installation_guide. See the chapter below concerning settings.
3. Start minikube or equivalent. In your terminal:

    minikube start 
   
4. Link docker to minikube:  
 
    eval $(minikube docker-env) 
  
5. Go to the folder containing the Dockerfile. Introduce your Github token to be able to download vectorbtpro with https. If you use ssh, adapt the line corresponding to this download in the Dockerfile.

    docker build . -t py-trading-bot --build-arg GH_TOKEN=<your Github Token\>

6. Change the password. Go in py-trading-bot/secret.yml and replace the items, especially the token for Telegram, with your values coded in base64, as it is the standard for secrets in Kubernetes.
7. Run 

    py-trading-bot/kubernetes/sequence_start_first_time.sh 
    
It is just some kubectl command in a sequence, you can also run them manually. Note that you may have to adapt the "kubectl" commands into "minikube kubectl".

8. Check that everything went well. All pods should be running.

    kubectl get pods

9. Expose the service 

    minikube service py-trading-bot-service --url
   
and click on the link to access the bot.

10. Start the background scheduler, including Telegram, by clicking on "start bot". Your telegram should display you "I'm back online". To connect to the admin panel, use the user "admin2" with password "abc1234".

Alternatively you can also start jupyter with:

    docker run --rm -p 8888:8888 -v "$PWD":/home/jovyan/work py-trading-bot

If you want to read the logs of the bot:

    kubectl logs <name of the worker pod>
 
Optional: Go in the admin panel and delete the user admin and testdb, that are completely unnecessary.
Note: The 

#Troubleshooting
If kubectl command is not found replace in the script the "kubectl" by "minikube kubectl -- ".
 
If for any reason the sequence_start_first_time.sh lead to an error, you need to clean properly Kubernetes before repeating the step. It means obviously removing the deployments with

    kubectl delete deployment <name of the deployment>
  
The jobs:

    kubectl delete job <name of the job>
    
And also the permanent volumes (it will kill your DB, use it only the very first time you install):

    kubectl delete pvc py-trading-bot-postgres-pvc
    kubectl delete pv py-trading-bot-postgres-pv
    
In addition, in kubernetes/postgres.yml, the hostPath under PersistentVolume

    hostPath:
      path: /data/py-trading-bot-postgres-pv
      
Needs to be changed, otherwise the same data will be loaded again when the permanent volumes are recreated.
 
    
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

# Settings
By default, only some settings can be adjusted after the docker image is built. If you want to variate more replace in settings.py: 
    
    _settings={
    "HARDCODED_SETTINGS":'abc',

 
through:

    _settings={
    "HARDCODED_SETTINGS":os.environ.get("HARDCODED_SETTINGS",<default value>),
    
you need then to adapt the file kubernetes/   configmap.yml under "data" with:

    hardcoded_settings : 'abc'
   
you need then to adapt the file kubernetes/django.yml under "-env" with:

    - name: HARDCODED_SETTINGS
        valueFrom:
          configMapKeyRef:
            name: py-trading-bot-configmap
            key: hardcoded_settings   

So you can change the value by each deployment of the container without rebuilding the image.

# Distribution
Obviously don't distribute this image anywhere as it would contain vectorbtpro which requires an appropriate license.


