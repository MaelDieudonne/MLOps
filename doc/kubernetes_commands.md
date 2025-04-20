Some usefull commands in the Kubernetes environment:
- To check running pods: `kubectl get pods`
- To remove the deployment: `kubectl delete deployment <deployment-name>` (removing the pod alone is useless as it keeps restarting)
- To release the domain name: `kubectl get ingress` / `kubectl delete ingress <ingress-name>`
- To inspect secrets: `kubectl get secret` / `kubectl get secret <secret-name> -o yaml` / `kubectl delete secret <secret-name>`
- To access the pod console: `kubectl exec -it <pod-name> -- /bin/sh` (then e.g. `pytest` to run tests)
- To erase everything but the db: `kubectl delete deployment test-movie-reviews-api-deployment test-movie-reviews-dashboard-deployment test-movie-reviews-tracker-deployment && kubectl delete ingress test-movie-reviews-ingress && kubectl delete secret test-movie-reviews-credentials`
- To remove the databse: `kubectl delete statefulset postgresql-<id_number>`
- To install everything at once: `chmod +x ./setup/create_db.sh && source ./setup/create_db.sh && chmod +x ./setup/create_kubectl_secrets.sh && source ./setup/create_kubectl_secrets.sh && kubectl apply -f deployment/ && kubectl get pods`