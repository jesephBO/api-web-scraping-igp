import requests
import boto3
import uuid
import json

def lambda_handler(event, context):
    # Endpoint directo que genera la tabla de reportes en la web del IGP
    url = "https://ultimosismo.igp.gob.pe/api/ultimo-sismo/reportes-sismicos"

    headers_req = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }

    # Realizar la solicitud HTTP
    response = requests.get(url, headers=headers_req, timeout=10)
    
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': json.dumps('Error al acceder a los datos del IGP')
        }

    data = response.json()
    
    # Extraer la lista de registros
    items = data if isinstance(data, list) else data.get('data', [])

    # Mapear las filas manteniendo los nombres de columnas de la web
    rows = []
    for item in items:
        rows.append({
            'Cod reporte': item.get('codigo', item.get('cod_reporte', '')),
            'Referencia': item.get('referencia', ''),
            'Semáforo': item.get('semaforo', ''),
            'Magnitud': str(item.get('magnitud', '')),
            'Fecha y hora de origen local': item.get('fecha_local', item.get('fecha_utc', ''))
        })

    # Guardar los datos en DynamoDB (Estructura idéntica a tu código original)
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('TablaWebScrapping')

    # Eliminar elementos antiguos
    scan = table.scan()
    with table.batch_writer() as batch:
        for each in scan.get('Items', []):
            batch.delete_item(
                Key={
                    'id': each['id']
                }
            )

    # Insertar los nuevos datos con la numeración i y el UUID
    i = 1
    for row in rows:
        row['#'] = i
        row['id'] = str(uuid.uuid4())
        table.put_item(Item=row)
        i = i + 1

    # Retornar la respuesta JSON limpia
    return {
        'statusCode': 200,
        'body': json.dumps(rows, ensure_ascii=False)
    }
