# py

import pandas as pd

from googleapiclient.discovery import build

from google_auth_oauthlib.flow import InstalledAppFlow

from google.auth.transport.requests import Request

from google.cloud import storage, bigquery

import pickle

import time

from datetime import datetime

from math import ceil

from dateutil.relativedelta import relativedelta

import os

# Scopes needed in GCP to perform actions in spreadsheets, consequently drive is included.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Mimes to allow the exploration of folders and manipulation of spreadsheets
mimes = {"folder": "application/vnd.google-apps.folder","sheet": "application/vnd.google-apps.spreadsheet"}

# Max rows allows per sheet (google sheets limit!)
max_rows_in_sheet = 500


def get_env_vars(var: str, envvar: str):

    if var is None:
        return os.environ[envvar]
    else:
        return var


def robust_dict_keys(d: dict, k, inverse=False):
    if inverse:
        d = {it: k for k, it in d.items()}
    if k not in d.keys():
        return k
    else:
        return d[k]


def google_api_creds(path2json_creds: str, gcp_config_path: str, SCOPES: list=SCOPES):
    """Shows basic usage of the Drive v3 API.
    Retrns the credentials of the user to access its GCP resources.
    """
    redefine_creds = False
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    try:
        with open(os.path.join(gcp_config_path, 'SCOPES.pickle'), 'rb') as scopes_file:
            prev_SCOPES = pickle.load(scopes_file)
    except(FileNotFoundError):
        prev_SCOPES = []
        redefine_creds = True

    if SCOPES != prev_SCOPES:
        redefine_creds = True

    if redefine_creds:
        # Keep track of SCOPES between runs
        with open(os.path.join(gcp_config_path, 'SCOPES.pickle'), 'wb') as scopes_file:
            pickle.dump(SCOPES, scopes_file)
        print("New scopes saved successfully: \n{}".format('\n'.join(SCOPES)))

    if os.path.exists(os.path.join(gcp_config_path, 'token.pickle')):
        with open(os.path.join(gcp_config_path, 'token.pickle'), 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid or redefine_creds:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(path2json_creds, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(os.path.join(gcp_config_path, 'token.pickle'), 'wb') as token:
            pickle.dump(creds, token)

    return creds


def view_folder(path2json_creds: str, gcp_config_path: str, parent_id: str = None):

    creds = google_api_creds(path2json_creds, gcp_config_path)

    assert creds is not None

    drive_service = build('drive', 'v3', credentials=creds)

    # Call the Drive v3 API
    if parent_id is None:
        results = drive_service.files().list(
            q="mimeType = 'application/vnd.google-apps.folder'",
            corpora='user',
            pageSize=10,
            fields="nextPageToken, files(id, name, mimeType)",
            includeItemsFromAllDrives=False,
            ).execute()
    else:
        assert type(parent_id) is str
        results = drive_service.files().list(
            q="'{}' in parents".format(parent_id),
            corpora='user',
            pageSize=10,
            fields="nextPageToken, files(id, name, mimeType)",
            includeItemsFromAllDrives=False,
            ).execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print(u'{0}: {1} ({2})'.format(robust_dict_keys(mimes, item['mimeType'], inverse=True), item['name'], item['id']))


def create_folder(path2json_creds: str, gcp_config_path: str, name: str, parent_id: list=[]):

    # id = token_hex(12)

    creds = google_api_creds(path2json_creds, gcp_config_path)

    assert creds is not None

    drive_service = build('drive', 'v3', credentials=creds)

    try:
        with open(os.path.join(gcp_config_path, 'GMAP_DRIVE_MAP.pickle'), 'rb') as drive_map:
            drive_ids = pickle.load(drive_map)
    except(FileNotFoundError):
        drive_ids = dict()

    # Call the Drive v3 API
    folder_metadata = {
        "name": name,
        "mimeType": mimes["folder"],
        "parents": parent_id
        }
    
    file = drive_service.files().create(
        body=folder_metadata,
        fields='id').execute()
    print('Folder ID: %s' % file.get('id'))

    drive_ids.update({(name, 'folder'): file.get('id')})

    with open(os.path.join(gcp_config_path, 'GMAP_DRIVE_MAP.pickle'), 'wb') as drive_map:
        pickle.dump(drive_ids, drive_map)


def create_sheet(path2json_creds: str, gcp_config_path: str, name: str, parent_id: list=[]):

    creds = google_api_creds(path2json_creds, gcp_config_path)

    assert creds is not None

    drive_service = build('drive', 'v3', credentials=creds)

    try:
        with open(os.path.join(gcp_config_path, 'GMAP_DRIVE_MAP.pickle'), 'rb') as drive_map:
            drive_ids = pickle.load(drive_map)
    except(FileNotFoundError):
        drive_ids = dict()

    # Call the Drive v3 API
    sheet_metadata = {
        "name": name,
        "mimeType": mimes["sheet"],
        "parents": parent_id
        }
    
    file = drive_service.files().create(
        body=sheet_metadata,
        fields='id').execute()
    print('Folder ID: %s' % file.get('id'))

    drive_ids.update({(name, 'sheet'): file.get('id')})

    with open(os.path.join(gcp_config_path, 'GMAP_DRIVE_MAP.pickle'), 'wb') as drive_map:
        pickle.dump(drive_ids, drive_map)


def write_stock_data(path2json_creds: str, gcp_config_path: str, fileId: str, tkr: str, initial_date: str, final_date: str):

    sheet_formula_str = """=GOOGLEFINANCE("{tkr}", "all", DATE({i_dt}), DATE({f_dt}), "DAILY")"""

    creds = google_api_creds(path2json_creds, gcp_config_path)

    assert creds is not None

    metadata = {
        "range": "Sheet1!A1",
        "majorDimension": "ROWS",
        "values": [
            [sheet_formula_str.format(
                tkr=tkr,
                i_dt=initial_date,
                f_dt=final_date,
            )],
        ],
    }

    # Call the Sheets API
    sheet_service = build('sheets', 'v4', credentials=creds)

    request = sheet_service.spreadsheets().values().update(
        spreadsheetId=fileId,
        range="Sheet1!A1",
        valueInputOption="USER_ENTERED",
        body=metadata
        )
    response = request.execute()


def read_stock_data(fileId: str, path2json_creds: str, gcp_config_path: str):

    creds = google_api_creds(path2json_creds, gcp_config_path)

    assert creds is not None

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=fileId, range="A1:F32").execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        return values


def generate_sheets_references(tkr: list, initial_date: str, final_date: str):

    max_cols_in_sheet=26

    row_spacing=(datetime.strptime(final_date, "%Y,%m,%d") - datetime.strptime(initial_date, "%Y,%m,%d")).days + 2

    col_spacing=6

    n_row=0

    n_col=0

    sheets_reference_structure = []

    sheets_reference_ranges = []

    for e, _ in enumerate(tkr):

        if (n_row+1)*row_spacing+1 > max_rows_in_sheet:
            n_row = 0
            n_col += 1
        
        if (n_col+1)*col_spacing > max_cols_in_sheet:
            print("Reached columns limit")
            break
        
        sheets_reference_structure.append(chr(ord('a') + n_col*col_spacing).upper() + str(n_row*row_spacing+1))

        sheets_reference_ranges.append(
            chr(ord('a') + n_col*col_spacing).upper() + str(n_row*row_spacing+1) + ":" +
            chr(ord('a') + (n_col+1)*col_spacing-1).upper() + str((n_row+1)*row_spacing)
            )

        n_row += 1
    
    return sheets_reference_structure, sheets_reference_ranges


def batch_write_stock_data(fileId: str, tkr: list, initial_date: str, final_date: str, path2json_creds: str, gcp_config_path: str):

    sheet_formula_str = """=GOOGLEFINANCE("{tkr}", "all", DATE({i_dt}), DATE({f_dt}), "DAILY")"""

    sheets_reference_structure, _ = generate_sheets_references(
        tkr=tkr,
        initial_date=initial_date,
        final_date=final_date
        )

    creds = google_api_creds(path2json_creds, gcp_config_path)

    assert creds is not None

    batch_update_values_request_body = {
        # How the input data should be interpreted.
        'value_input_option': 'USER_ENTERED',

        # The new values to apply to the spreadsheet.
        'data': [
            {
                "range": "Sheet1!{}".format(sheets_reference_structure[ii]),
                "majorDimension": "ROWS",
                "values": [
                    [sheet_formula_str.format(
                        tkr=stock,
                        i_dt=initial_date,
                        f_dt=final_date,
                    )],
                ],
            }
        for ii, stock in enumerate(tkr)],

        # Add desired entries to the request body.
        # "includeValuesInResponse": True # NOTE: Data loads too slow that a retrieving function is needed after writing is done
    }

    # # Call the Sheets API
    sheet_service = build('sheets', 'v4', credentials=creds)

    request = sheet_service.spreadsheets().values().clear(spreadsheetId=fileId, range='A1:Z{}'.format(max_rows_in_sheet))

    response = request.execute()

    request = sheet_service.spreadsheets().values().batchUpdate(
        spreadsheetId=fileId,
        body=batch_update_values_request_body
        )
    
    response = request.execute()

    values = response["responses"]

    return values


def batch_read_stock_data(fileId: str, tkr: list, initial_date: str, final_date: str, path2json_creds: str, gcp_config_path: str):

    _, sheets_reference_ranges = generate_sheets_references(
        tkr=tkr,
        initial_date=initial_date,
        final_date=final_date
        )

    creds = google_api_creds(path2json_creds, gcp_config_path)

    assert creds is not None

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().batchGet(
        spreadsheetId=fileId,
        ranges=sheets_reference_ranges,
        majorDimension="ROWS").execute()
    values = result.get('valueRanges', [])

    if not values:
        print('No data found.')
    else:
        return values


def google_finance_stocks(fileId: str, tkr: list, initial_date: str, final_date: str, path2json_creds: str, gcp_config_path: str):

    sheets_reference_structure, _ = generate_sheets_references(
        tkr=tkr,
        initial_date=initial_date,
        final_date=final_date
        )

    stocks = pd.DataFrame()

    loads = len(sheets_reference_structure)

    for ii in range(int(ceil(len(tkr)/loads))):

        tkrs = tkr[(loads*ii):(loads*(ii+1))]

        batch_write_stock_data(
            fileId=fileId,
            tkr=tkrs,
            initial_date=initial_date,
            final_date=final_date,
            path2json_creds=path2json_creds,
            gcp_config_path=gcp_config_path
            )

        time.sleep(3)

        cell_values = batch_read_stock_data(
            fileId=fileId,
            tkr=tkrs,
            initial_date=initial_date,
            final_date=final_date,
            path2json_creds=path2json_creds,
            gcp_config_path=gcp_config_path
            )

        errors = []
        for ii, r in enumerate(cell_values):
            if 'values' in r.keys():
                if '#N/A' in r['values'][0]:
                    errors.append(tkrs[ii])

        if not not errors:

            print('Could not retrieve the following tickers, please double check the names: {}'.format(', '.join(errors)))
        
        df = [
                pd.DataFrame(
                    r['values'][1:],
                    columns=r['values'][0]
                ).assign(Stock=tkrs[ii]) for ii, r in enumerate(cell_values) if ('values' in r.keys())&(tkrs[ii] not in errors)
            ]

        if not not df:

            df = pd.concat(
                df,
                ignore_index=True,
                axis=0
            )

            stocks = stocks.append(df)

    if not stocks.empty:
        stocks['Date'] = pd.to_datetime(stocks['Date'], format="%m/%d/%Y %H:%M:%S")

        for c in stocks.columns:
            if c not in ['Date', 'Stock']:
                stocks[c] = pd.to_numeric(stocks[c].replace("#N/A", None))

        return stocks

    else:

        return pd.DataFrame()


def delete_file(fileId, path2json_creds: str, gcp_config_path: str):

    creds = google_api_creds(path2json_creds, gcp_config_path)

    assert creds is not None

    drive_service = build('drive', 'v3', credentials=creds)

    try:
        with open(os.path.join(gcp_config_path, 'GMAP_DRIVE_MAP.pickle'), 'rb') as drive_map:
            drive_ids = pickle.load(drive_map)
    except(FileNotFoundError):
        drive_ids = dict()

    # Call the Drive v3 API    
    drive_service.files().delete(
        fileId=fileId
        ).execute()

    drive_ids = {k: it for k, it in drive_ids.items() if it != fileId}

    with open(os.path.join(gcp_config_path, 'GMAP_DRIVE_MAP.pickle'), 'wb') as drive_map:
        pickle.dump(drive_ids, drive_map)


def view_drive_map(return_: bool = False):
    with open(os.path.join(gcp_config_path, 'GMAP_DRIVE_MAP.pickle'), 'rb') as drive_map:
        drive_ids = pickle.load(drive_map)

    if return_:
        
        return drive_ids

    else:

        print(drive_ids)


# DONE: Upload blob
# DONE: Move to Bigtable
# DONE: Delete blob
# DONE: Check current state of stocks in GCP
# DONE: Program full procedure to upload data to GCP


def upload_stocks2blob(bucket_name: str, table_id: str, stocks_df: pd.DataFrame):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"
    source_file_name = '__temp__/stocks.csv'
    if not os.path.exists('__temp__'):
        os.makedirs('__temp__')
    stocks_df.to_csv(source_file_name)

    # table_id = os.environ['GCP_STOCK_TABLE']
    # bucket_name = os.environ['GCP_STOCK_BUCKET']

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(table_id)

    blob.upload_from_filename(source_file_name)

    os.remove(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, table_id
        )
    )


def download_blob(bucket_name: str, source_blob_name: str, destination_file_name: str):
    """Downloads a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # source_blob_name = "storage-object-name"
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client()

    # bucket_name = os.environ['GCP_STOCK_BUCKET']

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(
        "Blob {} downloaded to {}.".format(
            source_blob_name, destination_file_name
        )
    )


def gs_stocks(bucket_name:str, table_id:str, fields:str = "*", conds:str = "", stocks_df = True):
    # Construct a BigQuery client object.
    client = bigquery.Client()

    # table_id = os.environ['GCP_STOCK_TABLE']

    # Configure the external data source and query job.
    external_config = bigquery.ExternalConfig("CSV")
    external_config.source_uris = [
        f"gs://{bucket_name}/{table_id}"
    ]
    external_config.schema = [
        bigquery.SchemaField("IDX", "NUMERIC"),
        bigquery.SchemaField("Date", "DATETIME"),
        bigquery.SchemaField("Open", "FLOAT64"),
        bigquery.SchemaField("High", "FLOAT64"),
        bigquery.SchemaField("Low", "FLOAT64"),
        bigquery.SchemaField("Close", "FLOAT64"),
        bigquery.SchemaField("Volume", "FLOAT64"),
        bigquery.SchemaField("Stock", "STRING"),
    ]
    external_config.options.skip_leading_rows = 1
    job_config = bigquery.QueryJobConfig(table_definitions={table_id: external_config})

    sql="""SELECT {flds} FROM {tbl} {conds};""".format(tbl=table_id, flds=fields, conds=conds)

    query_job = client.query(sql, job_config=job_config)  # Make an API request.

    stocks = list(query_job)  # Wait for the job to complete.

    if stocks_df:
        stocks = pd.DataFrame().from_records(stocks,
            columns=['IDX', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Stock']).sort_values(["Date", "Stock"])
        # stocks = stocks.set_index(['IDX'])
        stocks = stocks.drop(columns=['IDX'])
    else:
        stocks = pd.DataFrame().from_records(stocks)

    return stocks


def sql_stocks(bucket_name:str, table_id:str, query: str):
    # Construct a BigQuery client object.
    client = bigquery.Client()

    # table_id = os.environ['GCP_STOCK_TABLE']

    # Configure the external data source and query job.
    external_config = bigquery.ExternalConfig("CSV")
    external_config.source_uris = [
        f"gs://{bucket_name}/{table_id}"
    ]
    external_config.schema = [
        bigquery.SchemaField("IDX", "NUMERIC"),
        bigquery.SchemaField("Date", "DATETIME"),
        bigquery.SchemaField("Open", "FLOAT64"),
        bigquery.SchemaField("High", "FLOAT64"),
        bigquery.SchemaField("Low", "FLOAT64"),
        bigquery.SchemaField("Close", "FLOAT64"),
        bigquery.SchemaField("Volume", "FLOAT64"),
        bigquery.SchemaField("Stock", "STRING"),
    ]
    external_config.options.skip_leading_rows = 1
    job_config = bigquery.QueryJobConfig(table_definitions={table_id: external_config})

    query_job = client.query(query, job_config=job_config)  # Make an API request.

    return query_job


def retrieve_stocks(
    fileId: str,
    tkr: list,
    initial_date: str,
    final_date: str,
    bucket_name: str,
    table_id: str
    ):

    open_final_date = str(datetime.strptime(final_date, "%Y,%m,%d") + relativedelta(days=1)).split(" ")[0]

    conds = '''WHERE DATE(Date) >= "{i_dt}" AND DATE(Date) <= "{f_dt}" AND Stock in ({stocks})'''.format(
        i_dt=initial_date.replace(",", "-")[:10],
        f_dt=open_final_date.replace(",", "-")[:10],
        stocks="'" + "', '".join(tkr) + "'")

    stocks = gs_stocks(bucket_name=bucket_name, table_id=table_id, fields=fields, conds=conds)

    existing_entries = stocks[["Date", "Stock"]].drop_duplicates()

    existing_entries["DetDate"] = existing_entries["Date"]

    existing_entries["Date"] = pd.to_datetime(existing_entries["DetDate"].astype(str).apply(lambda r: r.split(" ")[0]), format="%Y-%m-%d")

    existing_entries['IDX'] = existing_entries.apply(lambda r: tuple([r['Date'], r['Stock']]), axis=1)

    last_date = max(existing_entries.Date)

    first_date = min(existing_entries.Date)

    requested_dates = pd.DataFrame(
        {"Date": pd.date_range(
                start=initial_date.replace(",", "/"),
                end=final_date.replace(",", "/"),
                freq="B",
            )
        }
    ).assign(aux=1)

    requested_stocks = pd.DataFrame({"Stock": tkr}).assign(aux=1)

    requested_data = pd.merge(left=requested_dates, right=requested_stocks, on = "aux").drop(columns="aux")

    requested_data['IDX'] = requested_data.apply(lambda r: tuple([r['Date'], r['Stock']]), axis=1)

    requested_data["missing_data"] = ~requested_data.IDX.isin(existing_entries.IDX)

    equity_dates = pd.pivot_table(data=requested_data, values="missing_data", index = "Date", columns = "Stock")

    equity_dates = equity_dates.loc[:, [c for c in equity_dates.columns if ":" in c]]

    equity_dates = equity_dates.loc[~equity_dates.all(axis=1)].drop(columns=[c for c in equity_dates]).reset_index()

    requested_data = requested_data.loc[requested_data.Date.isin(equity_dates.Date)|(requested_data.Date > last_date)|(requested_data.Date < first_date)]

    missing_dates = (requested_data.groupby("Date").missing_data.sum() > len(requested_data.Stock.unique())*0.75).reset_index()

    missing_dates = missing_dates.loc[missing_dates.missing_data, "Date"]

    if len(missing_dates) < 5:
        print("missing_dates: {}".format(', '.join([str(x) for x in missing_dates.values])))
    else:
        print("missing_dates: {}".format(len(missing_dates)))

    missing_dates = requested_data.Date.isin(missing_dates)

    # missing_dates = (missing_dates.set_index("Date").missing_data.rolling(3).mean().bfill(0) > 2/3).reset_index()

    missing_stocks = (requested_data.loc[(requested_data.Date <= last_date)&(requested_data.Date >= first_date)].groupby("Stock").missing_data.sum() > len(requested_data.Date.unique())*0.75).reset_index()

    missing_stocks = missing_stocks.loc[missing_stocks.missing_data, "Stock"]

    if len(missing_stocks) < 5:
        print("missing_stocks: {}".format(', '.join([str(x) for x in missing_stocks.values])))
    else:
        print("missing_stocks: {}".format(len(missing_stocks)))

    missing_stocks = requested_data.Stock.isin(missing_stocks)

    data2load = requested_data.loc[missing_dates|missing_stocks]

    if not data2load.empty:

        last_download_template = pd.DataFrame(columns=["Date", "Stock"])[["Date", "Stock"]].drop_duplicates()

        for cut in [missing_stocks, missing_dates]:

            download_template = requested_data.loc[cut]

            if not download_template.empty:

                if download_template[["Date", "Stock"]].drop_duplicates().values != last_download_template[["Date", "Stock"]].drop_duplicates().values:

                    print("Retrieving missing data")

                    last_download_template = download_template.copy()

                    download_template = pd.pivot_table(data=download_template, values="missing_data", index = "Date", columns = "Stock")

                    download_template = download_template.reset_index()

                    download_template["1D"] = download_template.Date - min(download_template.Date)

                    download_template["2D"] = download_template["1D"].diff().dt.days.fillna(1)

                    download_template["breaks"] = download_template["2D"].apply(lambda x: x > 5).astype(int)

                    download_template["loads"] = download_template["breaks"].cumsum()

                    for ii in download_template.loads.unique():

                        download_metadata = download_template.loc[download_template.loads == ii]

                        start_date = str(min(download_metadata.Date)).replace("-", ",").split(" ")[0]

                        # end_date = str(max(download_metadata.Date) + relativedelta(days=1)).replace("-", ",").split(" ")[0]

                        end_date = str(max(download_metadata.Date)).replace("-", ",").split(" ")[0]

                        missing_stocks = [m for m in [c for c in download_metadata.columns if c in tkr] if download_metadata.loc[:, m].any()]

                        if start_date != end_date:

                            print(start_date, end_date, missing_stocks)

                            goog_stocks = google_finance_stocks(
                                fileId=fileId,
                                tkr=missing_stocks,
                                initial_date=start_date,
                                final_date=end_date,
                                path2json_creds=path2json_creds,
                                gcp_config_path=gcp_config_path
                                )

                            if goog_stocks is not None:

                                print("Data retreived")

                                stocks = stocks.append(goog_stocks).drop_duplicates().reset_index(drop=True)

                            if not stocks.empty:

                                upload_stocks2blob(bucket_name=bucket_name, table_id=table_id, stocks_df=stocks)

    print('Done')

    return stocks.sort_values(["Stock", "Date"])


# END