import requests
from bs4 import BeautifulSoup
import boto3
import uuid

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/productos/reportes-sismicos"

    headers_req = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    response = requests.get(url, headers=headers_req)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web del IGP'
        }

    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table')
    if not table:
        return {
            'statusCode': 404,
            'body': 'No se encontró la tabla de sismos en la página web'
        }

    headers = [header.text.strip() for header in table.find_all('th') if header.text.strip()]

    rows = []
    tr_elements = table.find_all('tr')[1:]  
    for row in tr_elements[:10]:
        cells = row.find_all('td')
        if cells:
            row_data = {}
            for i, cell in enumerate(cells):
                cell_text = cell.text.strip()
                if "Ver reporte" in cell_text:
                    continue                
                if i < len(headers):
                    col_name = headers[i]
                    row_data[col_name] = cell_text

            if row_data:
                rows.append(row_data)

    dynamodb = boto3.resource('dynamodb')
    table_db = dynamodb.Table('TablaSismosIGP')

    scan = table_db.scan()
    with table_db.batch_writer() as batch:
        for item in scan.get('Items', []):
            batch.delete_item(Key={'id': item['id']})

    for index, row in enumerate(rows, start=1):
        row['id'] = str(uuid.uuid4())
        row['#'] = str(index)
        table_db.put_item(Item=row)

    return {
        'statusCode': 200,
        'body': rows
    }