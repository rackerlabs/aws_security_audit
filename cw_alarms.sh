#!/bin/bash
# set -x
## Update alarm actions

os_team_arn="arn:aws:sns:eu-central-1:144888114082:boj-os_team"
network_team_arn="arn:aws:sns:eu-central-1:144888114082:boj-network_team"
dba_team_arn="arn:aws:sns:eu-central-1:144888114082:boj-dba_team"

existing_alarms_names=$(aws cloudwatch describe-alarms | grep "AlarmName" | grep "CPU" | awk -F'"' '{print $4}')

for alarm in $existing_alarms_names; do
    existing_alarm=$(aws cloudwatch describe-alarms --alarm-names $alarm)

    "$(echo $existing_alarm | jq .MetricAlarms[0].AlarmName)"
    "$(echo $existing_alarm | jq .MetricAlarms[0].AlarmDescription)"
    "$(echo $existing_alarm | jq .MetricAlarms[0].MetricName)"
    "$(echo $existing_alarm | jq .MetricAlarms[0].Namespace)"
    "$(echo $existing_alarm | jq .MetricAlarms[0].Period)"
    "$(echo $existing_alarm | jq .MetricAlarms[0].Threshold)"
    "$(echo $existing_alarm | jq .MetricAlarms[0].Dimensions[0].Name),Value=$(echo $existing_alarm | jq .MetricAlarms[0].Dimensions[0].Value)"
    "$(echo $existing_alarm | jq .MetricAlarms[0].EvaluationPeriods)"
    break

    aws cloudwatch put-metric-alarm \
        --alarm-name "$(echo $existing_alarm | jq .MetricAlarms[0].AlarmName)" \
        --alarm-description "$(echo $existing_alarm | jq .MetricAlarms[0].AlarmDescription)" \
        --metric-name "$(echo $existing_alarm | jq .MetricAlarms[0].MetricName)" \
        --namespace "$(echo $existing_alarm | jq .MetricAlarms[0].Namespace)" \
        --statistic "Average" \
        --period "$(echo $existing_alarm | jq .MetricAlarms[0].Period)" \
        --threshold "$(echo $existing_alarm | jq .MetricAlarms[0].Threshold)" \
        --comparison-operator "GreaterThanThreshold" \
        --dimensions "Name=$(echo $existing_alarm | jq .MetricAlarms[0].Dimensions[0].Name),Value=$(echo $existing_alarm | jq .MetricAlarms[0].Dimensions[0].Value)" \
        --evaluation-periods "$(echo $existing_alarm | jq .MetricAlarms[0].EvaluationPeriods)" \
        --alarm-actions "$os_team_arn" \
        --alarm-actions "$dba_team_arn"


    break
done
