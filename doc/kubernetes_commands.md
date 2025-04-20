Some usefull commands in the Kubernetes environment:
- To check running pods: `kubectl get pods`
- To remove the deployment: `kubectl delete deployment <deployment-name>` (removing the pod alone is useless as it keeps restarting)
- To remove the databse: `kubectl delete statefulset postgresql-<id_number>`
- To release the domain name: `kubectl get ingress` / `kubectl delete ingress <ingress-name>`
- To inspect secrets: `kubectl get secret` / `kubectl get secret <secret-name> -o yaml` / `kubectl delete secret <secret-name>`
- To access the pod console: `kubectl exec -it <pod-name> -- /bin/sh` (then e.g. `pytest` to run tests)
- To erase everything but the db: `kubectl delete deployment movie-reviews-api-deployment movie-reviews-dashboard-deployment movie-reviews-tracker-deployment && kubectl delete ingress movie-reviews-ingress && kubectl delete secret movie-reviews-credentials`