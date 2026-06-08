{{/*
Common labels applied to all resources.
*/}}
{{- define "kueue.labels" -}}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: kueue-operator
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
