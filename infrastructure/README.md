# Infrastructure (Azure, Terraform)

Creates the REES46 lake and warehouse on an Azure for Students subscription:
ADLS Gen2 (`raw`, `processed`), an Azure SQL server and a serverless database
on the **free offer** (auto-pauses when the monthly free amount is used; never
bills), and a $5 budget alert.

## Deploy

```bash
az login
export ARM_SUBSCRIPTION_ID=$(az account show --query id -o tsv)
cd infrastructure
terraform init
terraform plan -out=azure.tfplan -var operator_ip=$(curl -s https://api.ipify.org)
terraform apply azure.tfplan
```

The SQL admin password goes in `infrastructure/secret.auto.tfvars`
(gitignored, loaded automatically):

```hcl
sql_admin_password = "<16+ characters>"
```

State is local (`terraform.tfstate`, gitignored) and contains that password,
so never commit it.

## Firewall

Only your current public IP can reach the SQL server. If you change networks
and connections fail with a firewall error, re-run the `plan`/`apply` above;
`operator_ip` picks up your new address.
