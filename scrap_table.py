import requests
import boto3
import uuid

def lambda_handler(event, context):
    url = "https://ultimosismo.igp.gob.pe/api/reporte-sismico/ultimo-sismo"

    headers_req = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers_req)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la API del IGP'
        }

    data = response.json()
    
    rows = []
    items = data if isinstance(data, list) else data.get('data', [])

    for item in items:
        rows.append({
            'Cod reporte': item.get('codigo', ''),
            'Referencia': item.get('referencia', ''),
            'Semáforo': item.get('semaforo', ''),
            'Magnitud': item.get('magnitud', ''),
            'Fecha y hora de origen local': item.get('fecha_utc', item.get('fecha_hora', ''))
        })

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrapping')

    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan.get('Items', []):
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )

    i = 1
    for row in rows:
        row['#'] = i
        row['id'] = str(uuid.uuid4())  # Generar un ID único para cada entrada
        table.put_item(Item=row)
        i = i + 1

    return {
        'statusCode': 200,
        'body': rows
    }
