# Bronze Layer Data

## Overview

Bronze layer is raw layer, data source from Github archive ingest into ADLS gen2.
Data will be stored in Delta format with the following structure:

```
bronze/
├── year=YYYY/
│   ├── month=MM/
│   │   ├── day=DD/
│   │   │   ├── events_YYYYMMDD_HHMMSS.delta
│   │   │   └── _delta_log/

```