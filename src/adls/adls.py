import pandas as pd
import io 
from azure.storage.filedatalake import DataLakeServiceClient


class AzureDataLakeClient:
    def __init__(self, account_name: str, container_name: str, storage_key: str):
        if not storage_key:
            raise ValueError("Storage key is required to initialize AzureDataLakeClient.")
        
        self.account_name = account_name
        self.file_system_name = container_name
        self.storage_key = storage_key

        try:
            self.service_client = DataLakeServiceClient(
                account_url=f"https://{account_name}.dfs.core.windows.net",
                credential=storage_key
            )
            self.file_system_client = self.service_client.get_file_system_client(container_name)
        except Exception as e:
            raise ValueError(f"Error initializing AzureDataLakeClient: {e}")

    def close(self):
        self.service_client.close()

    def upload_dataframe(self, df: pd.DataFrame, remote_path: str, format='json'):
        try:
            output_buffer = io.BytesIO()

            if format == 'parquet':
                df.to_parquet(output_buffer, index=False)
            elif format == 'csv':
                df.to_csv(output_buffer, index=False, encoding='utf-8')
            elif format == 'json':
                df.to_json(output_buffer, orient='records', lines=True, force_ascii=False)
            else:
                raise ValueError("Format not supported. Use 'parquet', 'csv', or 'json'.")

            data = output_buffer.getvalue()
            file_client = self.file_system_client.get_file_client(remote_path)
            file_client.upload_data(data, overwrite=True)

        except Exception as e:
            raise ValueError(f"Error uploading dataframe: {e}")

    def get_dataframe(self, remote_path: str, format='parquet') -> pd.DataFrame:
        full_path = f"abfs://{self.file_system_name}/{remote_path}"

        storage_options = {
            "account_name": self.account_name,
            "account_key": self.storage_key
        }

        try:
            if format == 'parquet':
                df = pd.read_parquet(full_path, storage_options=storage_options)
            elif format == 'csv':
                df = pd.read_csv(full_path, storage_options=storage_options)
            elif format == 'json':
                df = pd.read_json(full_path, storage_options=storage_options, orient='records', lines=True)
            else:
                raise ValueError(f"Unsupported format: {format}")

            print(f"Loaded {len(df)} rows.")
            return df

        except Exception as e:
            print(f"Error reading dataframe: {e}")
            raise