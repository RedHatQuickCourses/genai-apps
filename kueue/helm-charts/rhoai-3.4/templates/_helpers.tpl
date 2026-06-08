{{/*
Common labels applied to all resources.
*/}}
{{- define "rhoai.labels" -}}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: rhoai-3.4-operators
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}
