python -c "
import pandas as pd
import requests
from io import BytesIO
import zipfile
from datetime import datetime, timedelta

date = datetime.now() - timedelta(days=1)
url = f'https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date.strftime(\"%Y%m%d\")}_F_0000.csv.zip'
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

if response.status_code == 200:
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        csv_filename = z.namelist()[0]
        df = pd.read_csv(z.open(csv_filename))
        print('Column names:')
        for col in df.columns:
            print(f'  - {col}')
        print(f'\nFirst row sample:')
        print(df.iloc[0].to_dict())
else:
    print('Could not download bhavcopy')
"
