MANUAL SETUP

PROJECT ID = {PROJECT_ID}

1: Enable required services
https://console.cloud.google.com/apis/dashboard - APIs and services managements
  https://console.cloud.google.com/marketplace/product/google/storage.googleapis.com?project={PROJECT_ID} - Cloud Storage API
  https://console.cloud.google.com/marketplace/product/google/drive.googleapis.com?project={PROJECT_ID} - Drive API
  https://console.cloud.google.com/marketplace/product/google/sheets.googleapis.com?project={PROJECT_ID} - Sheets API
  https://console.cloud.google.com/marketplace/product/google/bigquery.googleapis.com?project={PROJECT_ID} - Big Query API

2: Create storage bucket
2.1: Click on "CREATE BUCKET"
https://console.cloud.google.com/storage/browser - GCP Cloud Storage
name     = {GCP_BUCKET_NAME}
For location type select "Region" (budget option)
location = {GCP_LOCATION}
2.2: Under "Choose how to control access to objects" select "Fine grained"
2.3: Leave everything else as default
docs for google_storage_bucket: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket

3: Create storage object in bucket
3.1: Select "UPLOAD FILE" under the bucket created in step 3
bucket        = {GCP_BUCKET_NAME}
3.2: Upload the file created for the manual setup
file          = {CWD}/stocks

4: Create Big Query Dataset
https://console.cloud.google.com/bigquery - GCP Big Query
4.1: Click the 3 dots beside your current project ({PROJECT_ID}-XXXXXX) and select "Create dataset"
dataset_id                  = gfs_ds
location                    = {GCP_LOCATION}
Leave everything else as default
4.2: Select the created dataset, click "SHARING" and select "Permissions"
4.3: Select "Add Principal"
4.3.1: For "New principals" paste the Service Account email ({CLIENT_EMAIL})
4.3.2: For "Role" select "BigQuery Data Owner"

5: Create Big Query Table
Click the 3 dots beside the dataset created in step 4 (gfs_ds)and select "Create table"

5.1: "Source" section
5.1.1: For "Create table from" select "Google Cloud Storage"
5.1.2: Browse the "stocks" file in the bucket "{GCP_BUCKET_NAME}" (uri: {GCP_BUCKET_NAME}/stocks)
5.1.3: For "File format" select "CSV"

5.2: "Destination" section
5.2.1: "Project" - leave as default ({PROJECT_ID}-XXXXXX)
5.2.2: "Dataset" - leave as default (gfs_ds)
5.2.3: "Table" - stocks
5.2.2: "Table type" - leave as default (Native table)

5.3: "Schema" section
5.3.1: Enable "Edit as text"
5.3.2: Copy and paste the following:
[
  {{
    "name": "IDX",
    "type": "NUMERIC",
    "mode": "NULLABLE",
    "description": "Table index"
  }},
  {{
    "name": "Date",
    "type": "DATETIME",
    "mode": "NULLABLE",
    "description": "Date"
  }},
  {{
    "name": "Open",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Opening price"
  }},
  {{
    "name": "High",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Highest price"
  }},
  {{
    "name": "Low",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Lowest price"
  }},
  {{
    "name": "Close",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Closing price"
  }},
  {{
    "name": "Volume",
    "type": "FLOAT",
    "mode": "NULLABLE",
    "description": "Number of transactions"
  }},
  {{
    "name": "Stock",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Asset/Ticker name"
  }}
]

5.4: "Partition and cluster settings"
5.4.1: Leave everything as default

5.5: "Advanced options"
5.5.1: Under "Header rows to skip" write 1

5.6: Click "CREATE TABLE" 