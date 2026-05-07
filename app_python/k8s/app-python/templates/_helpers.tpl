{{- define "app-python.previewServiceName" -}}
{{- printf "%s-preview" (include "common.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end }}

{{- define "app-python.analysisTemplateName" -}}
{{- printf "%s-success-rate" (include "common.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end }}