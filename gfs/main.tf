variable "resource_tags" {
  description = "Tags to set for all resources"
  type        = map(string)
  default = {
    project     = "gfs-proyect",
    environment = "dev",
  }
}


# User defined variables for the GFS project
variable "project_id" {
  default     = "gfs-proyect"
  description = "The ID of the project for the GFS python package"
  type        = string
}

### select a location from https://cloud.google.com/storage/docs/locations
variable "gcp_location" {
  default     = "us-central1"
  description = "The location of the project an its components"
  type        = string
}

variable "gcp_zone" {
  default     = "us-central1-c"
  description = "The zone within the location for specific components like buckets, bigquery, etc."
  type        = string
}

variable "gcp_service_account_credentials_file" {
  default = "path/to/credentials"
}

variable "gcp_bucket_name" {
  default = "gfs-bucket"
}

locals {
  gcp_sa_json = file(var.gcp_service_account_credentials_file)
}

output "gcp_sa_email" {
  value = jsondecode(local.gcp_sa_json).client_email
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "3.5.0"
    }
  }
}

provider "google" {
  credentials = local.gcp_sa_json

  project = var.project_id
  region  = var.gcp_location
  zone    = var.gcp_zone
}

variable "gcp_service_list" {
  description = "The list of apis necessary for the project"
  type        = list(string)
  default = [
    "storage.googleapis.com",
    "drive.googleapis.com",
    "sheets.googleapis.com",
    "bigquery.googleapis.com"
  ]
}

resource "google_project_service" "gcp_services" {
  for_each                   = toset(var.gcp_service_list)
  project                    = var.project_id
  service                    = each.key
  disable_dependent_services = true
}

# docs for google_storage_bucket https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket
resource "google_storage_bucket" "gfs_bucket" {
  name     = var.gcp_bucket_name
  location = var.gcp_location
  depends_on = [
    google_project_service.gcp_services
  ]
}

resource "google_storage_bucket_object" "gfs_bucket_object" {
  name          = "stocks"
  bucket        = var.gcp_bucket_name
  source        = "stocks"
  content_type  = "application/octet-stream"
  storage_class = "NEARLINE"
  depends_on = [
    google_storage_bucket.gfs_bucket,
    google_project_service.gcp_services
  ]
}

resource "google_bigquery_dataset" "gfs_bq_dataset" {
  dataset_id                  = "gfs_ds"
  friendly_name               = "test"
  description                 = "This dataset is private"
  location                    = var.gcp_location

  labels = {
    env = var.resource_tags.environment
  }

  access {
    role          = "OWNER"
    user_by_email = jsondecode(local.gcp_sa_json).client_email
  }

  depends_on = [
    google_project_service.gcp_services
  ]
}

resource "google_bigquery_table" "stocks" {
  dataset_id = google_bigquery_dataset.gfs_bq_dataset.dataset_id
  table_id   = "stocks"

  labels = {
    env = var.resource_tags.environment
  }

  schema = <<EOF
[
  {
    "name": "IDX",
    "type": "NUMERIC",
    "mode": "NULLABLE",
    "description": "Table index"
  },
  {
    "name": "Date",
    "type": "DATETIME",
    "mode": "NULLABLE",
    "description": "Date"
  },
  {
    "name": "Open",
    "type": "FLOAT64",
    "mode": "NULLABLE",
    "description": "Opening price"
  },
  {
    "name": "High",
    "type": "FLOAT64",
    "mode": "NULLABLE",
    "description": "Highest price"
  },
  {
    "name": "Low",
    "type": "FLOAT64",
    "mode": "NULLABLE",
    "description": "Lowest price"
  },
  {
    "name": "Close",
    "type": "FLOAT64",
    "mode": "NULLABLE",
    "description": "Closing price"
  },
  {
    "name": "Volume",
    "type": "FLOAT64",
    "mode": "NULLABLE",
    "description": "Number of transactions"
  },
  {
    "name": "Stock",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Asset/Ticker name"
  }
]
EOF

  depends_on = [
    google_project_service.gcp_services,
    google_bigquery_dataset.gfs_bq_dataset
  ]

}