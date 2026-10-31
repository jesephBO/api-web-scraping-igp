import requests
import boto3
import uuid
from datetime import datetime

def lambda_handler(event, context):
    anio = datetime.now().year
    url = f"https://ultimosismo.igp.gob.pe/api/ultimo-sismo/ajaxb/{anio}"

    headers_req = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://ultimosismo.igp.gob.pe/productos/reportes-sismicos'
    }

    response = requests.get(url, headers=headers_req, timeout=15)
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': 'Error al acceder a la página web del IGP'
        }

    sismos = response.json()
    if not sismos:
        return {
            'statusCode': 404,
            'body': 'No se encontraron sismos en la página web'
        }


    sismos.sort(key=lambda s: s['codigo'], reverse=True)
    rows = []
    for sismo in sismos[:10]:
        fecha = datetime.strptime(sismo['fecha_local'][:10], '%Y-%m-%d').strftime('%d/%m/%Y')
        hora = sismo['hora_local'][11:19]

        row_data = {
            'Cod reporte': f"IGP/CENSIS/RS {sismo['codigo']}",
            'Referencia': str(sismo['referencia']),
            'Magnitud': str(sismo['magnitud']),
            'Fecha y hora de origen local': f"{fecha} {hora}",
            'Profundidad': str(sismo['profundidad']),
            'Latitud': str(sismo['latitud']),
            'Longitud': str(sismo['longitud']),
            'Intensidad': str(sismo['intensidad'])
        }
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