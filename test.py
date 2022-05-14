from gfs import google_finance

gcp_config_path='/path/to/gfs-config'
path2json_creds='path/to/creds.json'
path2json_service='path/to/service-account.json'

bucket_name='gft-dev-bucket'

if __name__ == '__main__':

    google_finance.terraform_setup(
        project_id='gft-test',
        project_env='dev',
        gcp_location='us-central1',
        gcp_zone='us-central1',
        gcp_bucket_name=bucket_name,
        service_account_json=path2json_service,
        terraform_apply=True
        )

    stocks = google_finance.retrieve_stocks(
        tkr=["NYSE:GOOG", "BMV:GOOG",],
        initial_date='2022,01,01',
        final_date='2022,01,10',
        path2json_service=path2json_service,
        path2json_creds=path2json_creds,
        gcp_config_path=gcp_config_path,
        bucket_name=bucket_name
        )

    print(stocks.head())