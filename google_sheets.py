# # TODO: Replace token.pickle when changing scopes
# # https://developers.google.com/identity/protocols/oauth2/scopes#drive

# # py

from __future__ import print_function

from pathlib import Path

from os import getcwd, environ

import os.path

from dotenv import load_dotenv

# This is not needed if loaded within the Docker container
# print([f for f in os.listdir(os.path.join(Path(), "../../.devcontainer/"))])
# load_dotenv(dotenv_path=os.path.join(Path(), "../../.devcontainer/devcontainer.env"))

from logging import error

import pickle

import time

from datetime import datetime

from pandas._libs import missing

from sqlalchemy import create_engine

import psycopg2

import pandas as pd

from numpy import ceil, nan

import json

from googleapiclient.discovery import build

from google_auth_oauthlib.flow import InstalledAppFlow

from google.auth.transport.requests import Request

from google.cloud import storage, bigquery

from dateutil.relativedelta import relativedelta

try:
    path2json_creds = os.path.join(Path('../'), environ["credentials_path"], environ["GOOGLE_DRIVE_CREDENTIALS"])
    path2json_apps = os.path.join(Path('../'), environ["credentials_path"], environ["GOOGLE_SERVICE_CREDENTIALS"])
    gcp_config_path = os.path.join(Path('../'), environ['gcp_path'])
    with open(os.path.join(gcp_config_path, 'google_apis_config.json'), 'rb') as scopes_file:
        gcp_config = json.load(scopes_file)

except(FileNotFoundError):
    path2json_creds = os.path.join(Path('/content'), environ["credentials_path"], environ["GOOGLE_DRIVE_CREDENTIALS"])
    path2json_apps = os.path.join(Path('/content'), environ["credentials_path"], environ["GOOGLE_SERVICE_CREDENTIALS"])
    gcp_config_path = os.path.join(Path('/content'), environ['gcp_path'])
    with open(os.path.join(gcp_config_path, 'google_apis_config.json'), 'rb') as scopes_file:
        gcp_config = json.load(scopes_file)

os.environ.update({'GOOGLE_APPLICATION_CREDENTIALS': path2json_apps})

SCOPES = gcp_config["SCOPES"]

mimes = gcp_config["mimes"]

max_rows_in_sheet = gcp_config["max_rows_in_sheet"]

def get_env_vars(var: str, envvar: str):

    if var is None:
        return environ[envvar]
    else:
        return var

def robust_dict_keys(d: dict, k, inverse=False):
    if inverse:
        d = {it: k for k, it in d.items()}
    if k not in d.keys():
        return k
    else:
        return d[k]

def google_api_creds(path2json_creds: str = path2json_creds, SCOPES: list=SCOPES, gcp_config_path: str=gcp_config_path):
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
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

def view_folder(parent_id: str = None):

    creds = google_api_creds()

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

def create_folder(name: str, parent_id: list=[]):

    # id = token_hex(12)

    creds = google_api_creds()

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

def create_sheet(name: str, parent_id: list=[]):

    creds = google_api_creds()

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

def write_stock_data(fileId: str, tkr: str, initial_date: str, final_date: str):

    sheet_formula_str = """=GOOGLEFINANCE("{tkr}", "all", DATE({i_dt}), DATE({f_dt}), "DAILY")"""

    creds = google_api_creds()

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

def read_stock_data(fileId: str):

    creds = google_api_creds()

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
    
    # max_rows_in_sheet=1000

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

    # sheets_reference_structure = [chr(ord('a') + c*6).upper() + str(r*33 + 1) for c in range(int(26/6)) for r in range(int(max_rows_in_sheet/33))]

    # sheets_reference_ranges = [chr(ord('a') + c*6).upper() + str(r*33 + 1) + ":" + chr(ord('a') + (c+1)*6 - 1).upper() + str((r+1)*33) for c in range(int(26/6)) for r in range(int(max_rows_in_sheet/33))]
    
    return sheets_reference_structure, sheets_reference_ranges

def batch_write_stock_data(fileId: str, tkr: list, initial_date: str, final_date: str):

    sheet_formula_str = """=GOOGLEFINANCE("{tkr}", "all", DATE({i_dt}), DATE({f_dt}), "DAILY")"""

    sheets_reference_structure, _ = generate_sheets_references(
        tkr=tkr,
        initial_date=initial_date,
        final_date=final_date
        )

    creds = google_api_creds()

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

def batch_read_stock_data(fileId: str, tkr: list, initial_date: str, final_date: str):

    _, sheets_reference_ranges = generate_sheets_references(
        tkr=tkr,
        initial_date=initial_date,
        final_date=final_date
        )

    creds = google_api_creds()

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

def google_finance_stocks(
    fileId: str,
    tkr: list,
    initial_date: str,
    final_date: str
    ):

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
            final_date=final_date
            )

        time.sleep(3)

        cell_values = batch_read_stock_data(
            fileId=fileId,
            tkr=tkrs,
            initial_date=initial_date,
            final_date=final_date
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
                stocks[c] = pd.to_numeric(stocks[c].replace("#N/A", nan))

        return stocks

    else:

        return pd.DataFrame()

def delete_file(fileId):

    creds = google_api_creds()

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

def save_stocks2pgs(df: pd.DataFrame, table: str = None, db: str = None, usr: str = None, pwd: str = None, inst: str = None, port: str = None, replace=False):

    inst = get_env_vars(var=inst, envvar='PSG_instance')
    port = get_env_vars(var=port, envvar='PSG_localport')
    table = get_env_vars(var=table, envvar='PSG_FINRL_TABLE')
    db = get_env_vars(var=db, envvar='PSG_DB')
    usr = get_env_vars(var=usr, envvar='PSG_USR')
    pwd = get_env_vars(var=pwd, envvar='PSG_PWD')
    
    engine = create_engine('postgresql://{usr}:{pwd}@{inst}:{port}/{db}'.format(usr=usr, pwd=pwd, inst=inst, port=port, db=db))

    try:

        con = engine.connect()    

    except(psycopg2.OperationalError):

        raise(psycopg2.OperationalError)

    if replace:

        df.to_sql(table, con, if_exists="replace", index=False)

        print('Table replaced with {} entries'.format(len(df)))

    else:

        existing_entries = pd.read_sql_query(sql="""SELECT DISTINCT "Date", "Stock" FROM {tbl} ORDER BY "Stock", "Date";""".format(tbl=table), con=con)

        existing_entries['IDX'] = existing_entries.apply(lambda r: tuple([r['Date'], r['Stock']]), axis=1)

        current_entries = df.apply(lambda r: tuple([r['Date'], r['Stock']]), axis=1)

        new_entries = df.loc[~current_entries.isin(existing_entries.IDX)].drop_duplicates().reset_index(drop=True)

        if not new_entries.empty:

            new_entries.to_sql(table, con, if_exists="append", index=False)

            print('{} new entries saved'.format(len(new_entries)))

        else:

            print('No new entries')

    con.close()

    return 200

def load_stocks2pgs(table: str = None, db: str = None, usr: str = None, pwd: str = None, fields: str = "*", conds: str = "", inst: str = None, port: str  = None):

    inst = get_env_vars(var=inst, envvar='PSG_instance')
    port = get_env_vars(var=port, envvar='PSG_localport')
    table = get_env_vars(var=table, envvar='PSG_FINRL_TABLE')
    db = get_env_vars(var=db, envvar='PSG_DB')
    usr = get_env_vars(var=usr, envvar='PSG_USR')
    pwd = get_env_vars(var=pwd, envvar='PSG_PWD')
    
    engine = create_engine('postgresql://{usr}:{pwd}@{inst}:{port}/{db}'.format(usr=usr, pwd=pwd, inst=inst, port=port, db=db))
    
    con = engine.connect()

    existing_entries = pd.read_sql_query(sql="""SELECT {flds} FROM {tbl} {conds} ORDER BY "Stock", "Date";""".format(tbl=table, flds=fields, conds=conds), con=con)

    con.close()

    return existing_entries

# TODO: Program full procedure to upload data to GCP
# Check current stocks (IDEA: use gs_stocks function bellow)
# DONE: Upload blob
# DONE: Move to Bigtable
# DONE: Delete blob

def upload_stocks2blob(stocks_df: pd.DataFrame):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"
    source_file_name = '__temp__/stocks.csv'
    if not os.path.exists('__temp__'):
        os.makedirs('__temp__')
    stocks_df.to_csv(source_file_name)

    storage_client = storage.Client()
    bucket = storage_client.bucket(environ['GCP_STOCK_BUCKET'])
    blob = bucket.blob(environ['GCP_STOCK_TABLE'])

    blob.upload_from_filename(source_file_name)

    os.remove(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, environ['GCP_STOCK_TABLE']
        )
    )

def download_blob(source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # source_blob_name = "storage-object-name"
    # destination_file_name = "local/path/to/file"

    storage_client = storage.Client()

    bucket = storage_client.bucket(environ['GCP_STOCK_BUCKET'])

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

def gs_stocks(fields:str = "*", conds:str = "", stocks_df = True):
    # Construct a BigQuery client object.
    client = bigquery.Client()

    table_id = environ['GCP_STOCK_TABLE']

    # Configure the external data source and query job.
    external_config = bigquery.ExternalConfig("CSV")
    external_config.source_uris = [
        "gs://finrl_rlws/stocks"
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

def sql_stocks(query):
    # Construct a BigQuery client object.
    client = bigquery.Client()

    table_id = environ['GCP_STOCK_TABLE']

    # Configure the external data source and query job.
    external_config = bigquery.ExternalConfig("CSV")
    external_config.source_uris = [
        "gs://finrl_rlws/stocks"
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
    GCP=False,
    table: str=None, db: str=None, usr: str=None, pwd: str=None, fields: str = "*", conds: str = "", inst: str=None, port: str=None):

    open_final_date = str(datetime.strptime(final_date, "%Y,%m,%d") + relativedelta(days=1)).split(" ")[0]

    if GCP:
        conds = '''WHERE DATE(Date) >= "{i_dt}" AND DATE(Date) <= "{f_dt}" aND Stock in ({stocks})'''.format(
            i_dt=initial_date.replace(",", "-")[:10],
            f_dt=open_final_date.replace(",", "-")[:10],
            stocks="'" + "', '".join(tkr) + "'")

        stocks = gs_stocks(fields=fields, conds=conds)
    else:
        conds = """WHERE "Date" >= '{i_dt}' AND "Date" <= '{f_dt}' AND "Stock" in ({stocks})""".format(
            i_dt=initial_date.replace(",", "/"),
            f_dt=open_final_date.replace(",", "/"),
            stocks="'" + "', '".join(tkr) + "'")

        stocks = load_stocks2pgs(fields=fields, conds=conds)

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
                                final_date=end_date
                                )

                            if goog_stocks is not None:

                                print("Data retreived")

                                stocks = stocks.append(goog_stocks).drop_duplicates().reset_index(drop=True)

                            if not stocks.empty:

                                # try:

                                #     save_stocks2pgs(df=stocks, table=table, db=db, usr=usr, pwd=pwd, inst=inst, port=port, replace=False)

                                # except(psycopg2.OperationalError) as e:

                                #     print(e)

                                if GCP:

                                    upload_stocks2blob(stocks_df=stocks)

    print('Done')

    return stocks.sort_values(["Stock", "Date"])
