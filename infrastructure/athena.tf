# ========================================
# Athena over the REES46 events lake
# ========================================
# Partition projection computes event_date partitions from the S3 path
# template, so no crawler or MSCK REPAIR / ADD PARTITION step is needed.

locals {
  processed_bucket = aws_s3_bucket.data_lake_buckets["processed"].bucket
  events_location  = "s3://${local.processed_bucket}/rees46/events"
}

resource "aws_glue_catalog_database" "rees46_raw" {
  name        = "rees46_raw"
  description = "Raw REES46 e-commerce events (Parquet, one partition per UTC day)"
}

resource "aws_glue_catalog_table" "events" {
  name          = "events"
  database_name = aws_glue_catalog_database.rees46_raw.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL                              = "TRUE"
    classification                        = "parquet"
    "projection.enabled"                  = "true"
    "projection.event_date.type"          = "date"
    "projection.event_date.format"        = "yyyy-MM-dd"
    "projection.event_date.range"         = "2019-10-01,2019-11-30"
    "projection.event_date.interval"      = "1"
    "projection.event_date.interval.unit" = "DAYS"
    "storage.location.template"           = "${local.events_location}/event_date=$${event_date}/"
  }

  partition_keys {
    name = "event_date"
    type = "string"
  }

  storage_descriptor {
    location      = "${local.events_location}/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "event_key"
      type = "string"
    }
    columns {
      name = "event_time"
      type = "timestamp"
    }
    columns {
      name = "event_type"
      type = "string"
    }
    columns {
      name = "product_id"
      type = "bigint"
    }
    columns {
      name = "category_id"
      type = "bigint"
    }
    columns {
      name = "category_code"
      type = "string"
    }
    columns {
      name = "brand"
      type = "string"
    }
    columns {
      name = "price"
      type = "decimal(10,2)"
    }
    columns {
      name = "user_id"
      type = "bigint"
    }
    columns {
      name = "user_session"
      type = "string"
    }
  }
}

resource "aws_athena_workgroup" "dev" {
  name          = "${var.project_name}-dev"
  force_destroy = true

  configuration {
    enforce_workgroup_configuration = true
    # Guardrail: no single query may scan more than 10 GB (~$0.05).
    bytes_scanned_cutoff_per_query = 10737418240

    result_configuration {
      output_location = "s3://${local.processed_bucket}/athena-results/dev/"
    }
  }
}

output "glue_database_name" {
  description = "Glue database holding the raw REES46 events table"
  value       = aws_glue_catalog_database.rees46_raw.name
}

output "athena_workgroup_name" {
  description = "Athena workgroup for ad-hoc and dev queries"
  value       = aws_athena_workgroup.dev.name
}
