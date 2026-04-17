{{/*
Common template helpers for weaviate-operator
*/}}
{{- define "weaviate-operator.name" -}}
{{- default .Chart.Name .Values.nameOverride -}}
{{- end -}}

{{- define "weaviate-operator.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride -}}
{{- else -}}
{{- printf "%s-%s" (include "weaviate-operator.name" .) .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
