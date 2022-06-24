from gfs import google_finance

if __name__ == '__main__':

    gcp_config_path=input('path to folder where config files will be stored: ')
    path2json_creds=input('path to credentials json file for the OAuth webapp authorization: ')
    path2json_service=input('path to service account json file: ')

    bucket_name=input('GCP bucket name: ')
    project_id=input('GCP project_id: ')
    project_location=input('GCP project location: ')

    try:
        print("Automated GCP setup")
        google_finance.terraform_setup(
            project_id=project_id,
            project_env='dev',
            gcp_location=project_location,
            gcp_zone=project_location,
            gcp_bucket_name=bucket_name,
            service_account_json=path2json_service,
            terraform_apply=True
        )
    except:
        print("Switched to manual GCP setup, follow instructions under 'manual_setup.txt'")
        google_finance.generate_setup_files(
            project_id=project_id,
            project_env='dev',
            gcp_location=project_location,
            gcp_zone=project_location,
            service_account_json=path2json_service,
            gcp_bucket_name=bucket_name
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