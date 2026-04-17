{{/* Helper to build a fullname */}}
{{- define "fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride }}
{{- else }}
{{- $name := printf "%s-%s" .Release.Name .Chart.Name | lower | replace "." "-" }}
{{- $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
