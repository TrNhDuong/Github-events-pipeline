from src.ingestion.ingest import ingest_hour
from src.adls.adls import AzureDataLakeClient
from src.core.config_loader import ConfigLoader 
import pandas as pd
 

def bronze_layer_execution(day: int, month: int, year: int, hour: int):
    storage_key = dbutils.secrets.get(scope="storage_secret", key="storage_key")

    date_str = f"{year:04d}-{month:02d}-{day:02d}"

    loader = ConfigLoader()
    account_config = loader.load("account/account.yml")
    bronze_config = loader.load("bronze/bronze.yml") 

    account = account_config["source"]["account"]
    container = account_config["source"]["container"]
    directory = bronze_config["destination"]["path"]       

    try: 
        github_events_data = pd.DataFrame(ingest_hour(date_str, hour))
    except Exception as e:
        raise ValueError(f"Error ingesting data for {date_str} hour {hour}: {e}")
    
    try: 
        adls_client = AzureDataLakeClient(account, container, storage_key)
    except Exception as e:
        raise ValueError(f"Error initializing AzureDataLakeClient: {e}")
    
    try: 
        adls_client.upload_dataframe(github_events_data, f"{directory}/{year}/{month:02d}/{day:02d}/{hour:02d}.json", format="json")
    except Exception as e:
        raise ValueError(f"Error uploading data to ADLS for {date_str} hour {hour}: {e}")
    
    adls_client.close()

    print(f"Ingested and stored data for {date_str} hour {hour:02d} in Bronze layer")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--year",  type=int)
    parser.add_argument("--month", type=int)
    parser.add_argument("--day",   type=int)
    parser.add_argument("--hour",  type=int)
    args = parser.parse_args()

    bronze_layer_execution(args.day, args.month, args.year, args.hour)
