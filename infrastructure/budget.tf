# Early warning only: Azure for Students has no card attached, so spending
# stops at the credit anyway (spec §10).
data "azurerm_subscription" "current" {}

resource "azurerm_consumption_budget_subscription" "monthly" {
  name            = "budget-${var.project}"
  subscription_id = data.azurerm_subscription.current.id
  amount          = 5
  time_grain      = "Monthly"

  time_period {
    start_date = "2026-09-01T00:00:00Z"
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThan"
    threshold_type = "Actual"
    contact_emails = [var.alert_email]
  }
}
