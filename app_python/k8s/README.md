# Lab 9 - Kubernetes Fundamentals

## Local Kubernetes Setup
I chose `minikube` for local k8s deployment.

```bash
$ minikube start
$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:53527
CoreDNS is running at https://127.0.0.1:53527/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   74s   v1.35.1
```

## Application Deployment
Manifests `deployment.yaml` and `service.yaml`.

```bash
$ kubectl apply -f deployment.yaml
deployment.apps/app-python created

$ kubectl apply -f service.yaml
service/app-python created

$ kubectl get all
NAME                              READY   STATUS    RESTARTS   AGE
pod/app-python-db878b65c-7drgn    1/1     Running   0          45s
pod/app-python-db878b65c-fn76l    1/1     Running   0          52s
pod/app-python-db878b65c-n57bf    1/1     Running   0          60s

NAME                 TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/app-python   NodePort    10.109.255.246   <none>        8080:30080/TCP   0s
service/kubernetes   ClusterIP   10.96.0.1        <none>        443/TCP          3m52s

NAME                         READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/app-python   3/3     3            3           0s

NAME                                    DESIRED   CURRENT   READY   AGE
replicaset.apps/app-python-db878b65c    3         3         3       0s

$ kubectl describe deployment app-python
Name:                   app-python
Namespace:              default
Selector:               app=app-python
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app=app-python
  Containers:
   app-python:
    Image:      ssspamqe/devops-info-service:latest
    Port:       8080/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     200m
      memory:  128Mi
    Requests:
      cpu:         100m
      memory:      64Mi
    Liveness:      http-get http://:8080/ delay=15s timeout=1s period=10s #success=1 #failure=3
    Readiness:     http-get http://:8080/ delay=5s timeout=1s period=5s #success=1 #failure=3
```

## Scaling and Updates
```bash
$ kubectl scale deployment/app-python --replicas=5
deployment.apps/app-python scaled

$ kubectl get pods
NAME                         READY   STATUS    RESTARTS   AGE
app-python-db878b65c-7drgn   1/1     Running   0          7m44s
app-python-db878b65c-fn76l   1/1     Running   0          7m51s
app-python-db878b65c-k9dcv   1/1     Running   0          5s
app-python-db878b65c-n57bf   1/1     Running   0          7m59s
app-python-db878b65c-nchmf   1/1     Running   0          5s
```

Triggering a rolling update using `TEST_ENV=rollout_test`:
```bash
$ kubectl set env deployment/app-python TEST_ENV=rollout_test
deployment.apps/app-python env updated

$ kubectl rollout status deployment/app-python
Waiting for deployment "app-python" rollout to finish: 1 out of 5 new replicas have been updated...
...
deployment "app-python" successfully rolled out

$ kubectl rollout history deployment/app-python 
deployment.apps/app-python 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>

$ kubectl rollout undo deployment/app-python
deployment.apps/app-python rolled back
```

## Ingress with TLS (Bonus)

Enabled `ingress` addon:
```bash
$ minikube addons enable ingress
```

Apply Second App and ingress route:
```bash
$ kubectl apply -f app-go.yaml
deployment.apps/app-go created
service/app-go created

$ openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout certs/tls.key -out certs/tls.crt -subj "/CN=local.example.com/O=local.example.com"
$ kubectl create secret tls tls-secret --key certs/tls.key --cert certs/tls.crt
secret/tls-secret created

$ kubectl apply -f ingress.yaml
ingress.networking.k8s.io/apps-ingress created
```

Testing the Ingress rule via URL routing (assumes `minikube tunnel` is executing in the background and `/etc/hosts` mapped to 127.0.0.1 for local.example.com):
```bash
$ curl -k https://local.example.com/app1
<App1 Payload>
$ curl -k https://local.example.com/app2
<App2 Payload>
```
