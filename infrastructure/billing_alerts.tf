# ========================================
# AWS CloudWatch Billing Alerts
# ========================================
# IMPORTANT: These resources MUST be created in us-east-1
# Billing metrics are only available in us-east-1 region
# ========================================

# ==========================================
# SNS Topic for Billing Alerts
# ==========================================
resource "aws_sns_topic" "billing_alerts" {
  name     = "billing-alerts" # Simple name for portfolio project
  provider = aws.us-east-1

  display_name = "AWS Billing Alerts"

  tags = {
    Name    = "Billing Alerts SNS Topic"
    Purpose = "Cost Monitoring"
  }
}

# ==========================================
# SNS Email Subscription
# ==========================================
resource "aws_sns_topic_subscription" "billing_alerts_email" {
  topic_arn = aws_sns_topic.billing_alerts.arn
  protocol  = "email"
  endpoint  = var.billing_alert_email
  provider  = aws.us-east-1
}

# ==========================================
# CloudWatch Billing Alarm: $1 Threshold
# ==========================================
resource "aws_cloudwatch_metric_alarm" "billing_alarm_1" {
  alarm_name          = "BillingAlert-1USD"
  alarm_description   = "Alert when AWS charges exceed $1 - Early warning for cost monitoring"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600 # 6 hours (minimum for billing metrics)
  statistic           = "Maximum"
  threshold           = 1.0
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency = "USD"
  }

  alarm_actions = [aws_sns_topic.billing_alerts.arn]

  provider = aws.us-east-1

  tags = {
    Name      = "Billing Alert 1USD"
    Severity  = "Low"
    Threshold = "1USD"
  }
}

# ==========================================
# CloudWatch Billing Alarm: $5 Threshold
# ==========================================
resource "aws_cloudwatch_metric_alarm" "billing_alarm_5" {
  alarm_name          = "BillingAlert-5USD"
  alarm_description   = "Alert when AWS charges exceed $5 - Review costs and optimize"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600
  statistic           = "Maximum"
  threshold           = 5.0
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency = "USD"
  }

  alarm_actions = [aws_sns_topic.billing_alerts.arn]

  provider = aws.us-east-1

  tags = {
    Name      = "Billing Alert 5USD"
    Severity  = "Medium"
    Threshold = "5USD"
  }
}

# ==========================================
# CloudWatch Billing Alarm: $10 Threshold
# ==========================================
resource "aws_cloudwatch_metric_alarm" "billing_alarm_10" {
  alarm_name          = "BillingAlert-10USD"
  alarm_description   = "CRITICAL: AWS charges exceed $10 - Immediate action required"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600
  statistic           = "Maximum"
  threshold           = 10.0
  treat_missing_data  = "notBreaching"

  dimensions = {
    Currency = "USD"
  }

  alarm_actions = [aws_sns_topic.billing_alerts.arn]

  provider = aws.us-east-1

  tags = {
    Name      = "Billing Alert 10USD"
    Severity  = "High"
    Threshold = "10USD"
  }
}

# ==========================================
# Outputs
# ==========================================
output "billing_alert_topic_arn" {
  description = "ARN of the SNS topic for billing alerts"
  value       = aws_sns_topic.billing_alerts.arn
}

output "billing_alarms" {
  description = "Names of created billing alarms"
  value = {
    alarm_1usd  = aws_cloudwatch_metric_alarm.billing_alarm_1.alarm_name
    alarm_5usd  = aws_cloudwatch_metric_alarm.billing_alarm_5.alarm_name
    alarm_10usd = aws_cloudwatch_metric_alarm.billing_alarm_10.alarm_name
  }
}

output "billing_alert_email" {
  description = "Email address receiving billing alerts"
  value       = var.billing_alert_email
  sensitive   = true # Don't display in plan output
}

# ==========================================
# Cost Estimation
# ==========================================
# CloudWatch Alarms: 
# - First 10 alarms: FREE
# - After 10 alarms: $0.10/alarm/month
# 
# SNS:
# - First 1,000 email notifications: FREE
# - After 1,000: $2 per 100,000 emails
#
# Total cost for 3 alarms + SNS: $0/month (within free tier)
# ==========================================