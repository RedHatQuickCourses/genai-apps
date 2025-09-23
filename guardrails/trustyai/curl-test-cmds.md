# Testing curl commands

## Without Guardrails - test input

```shell
curl -s -X 'POST' \
  "http://granite-33-2b-instruct-predictor.trustyai-demo.svc.cluster.local:8080/v1/chat/completions" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
   "model": "granite-33-2b-instruct",
   "messages": [
     {
       "content": "Who are you? Who created you?",
       "role": "user"
     }
   ]
}' | jq
```


## With Guardrails - safe input

```shell
curl -s -X 'POST' \
 "http://gorch-service.trustyai-demo.svc.cluster.local:8033/api/v2/chat/completions-detection" \
 -H 'accept: application/json' \
 -H 'Content-Type: application/json' \
 -d '{
   "model": "granite-33-2b-instruct",
   "messages": [
       {
           "content": "Who are you? Who created you?",
           "role": "user"
       }
   ],
   "detectors": {
       "input": {
           "hap": {}
       },
       "output": {
           "hap": {}
       }
   }
}' | jq
```

## With Guardrails - unsafe input

```shell
curl -s -X 'POST' \
 "http://gorch-service.trustyai-demo.svc.cluster.local:8033/api/v2/chat/completions-detection" \
 -H 'accept: application/json' \
 -H 'Content-Type: application/json' \
 -d '{
   "model": "granite-33-2b-instruct",
   "messages": [
       {
           "content": "You bird-brained moron. I hope you rot in hell.",
           "role": "user"
       }
   ],
   "detectors": {
       "input": {
           "hap": {}
       },
       "output": {
           "hap": {}
       }
   }
}' | jq
```

## With Guardrails Gateway Health check
$ ORCH_ROUTE_HEALTH=$(oc get routes guardrails-orchestrator-health -o jsonpath='{.spec.host}')
$ curl -s https://$ORCH_ROUTE_HEALTH/info | jq

## With Guardrails Gateway
$ GUARDRAILS_GATEWAY=https://$(oc get routes guardrails-gateway -o jsonpath='{.spec.host}')
$ python prompt.py \
  --url $GUARDRAILS_GATEWAY/passthrough/v1/chat/completions \
  --model granite-33-2b-instruct \
  --message "I hate Klingons. They are disgusting"