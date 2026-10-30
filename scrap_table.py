import requests
from bs4 import BeautifulSoup
import boto3
import uuid
import json

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/ultimo-sismo/reportes-sismicos"

    headers_req = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9'
    }

    response = requests.get(url, headers=headers_req, timeout=10)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': json.dumps('Error al acceder a la página web del IGP')
        }

    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table')
    if not table:
        return {
            'statusCode': 404,
            'body': json.dumps('No se encontró la tabla en la página web')
        }

    headers = [header.text.strip() for header in table.find_all('th')]

    rows = []
    for row in table.find_all('tr')[1:]:  # Omitir el encabezado
        cells = row.find_all('td')
        if cells:
            row_data = {}
            for i, cell in enumerate(cells):
                if (i + 1) < len(headers):
                    header_name = headers[i + 1]
                    row_data[header_name] = cell.text.strip()
            if row_data:
                rows.append(row_data)

    dynamodb = boto3.resource('dynamodb')
    table_db = dynamodb.Table('TablaWebScrapping')

    scan = table_db.scan()
    with table_db.batch_writer() as batch:
        for each in scan.get('Items', []):
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )

    i = 1
    for row in rows:
        row['#'] = i
        row['id'] = str(uuid.uuid4())
        table_db.put_item(Item=row)
        i = i + 1

    return {
        'statusCode': 200,
        'body': json.dumps(rows, ensure_ascii=False)
    }
