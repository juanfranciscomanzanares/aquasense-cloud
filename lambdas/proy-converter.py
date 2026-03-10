import json
import boto3
import csv
import io
from datetime import datetime
import urllib.parse

s3 = boto3.client('s3')

PROCESSED_BUCKET_NAME = 'proy-processed-json' 

def lambda_handler(event, context):
    try:
        # 1. Obtener bucket y key
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        
        print(f"Procesando archivo: {key}")
        
        # 2. Descargar el fichero
        response = s3.get_object(Bucket=source_bucket, Key=key)
        
        # Usamos utf-8-sig para evitar problemas con caracteres raros (BOM) de Excel
        csv_content = io.TextIOWrapper(response['Body'], encoding='utf-8-sig')
        
        # 3. Leer CSV
        reader = csv.DictReader(csv_content)
        data_list = []
        
        for row in reader:
            # Limpieza básica
            fecha_str = row['Fecha'].strip()
            
            # Saltamos si leemos una cabecera repetida por error
            if fecha_str == 'Fecha':
                continue
            
            try:
                dt_obj = datetime.strptime(fecha_str, '%Y/%m/%d')
                full_date = dt_obj.strftime('%Y-%m-%d')
                
            except ValueError as e:
                # Si falla, lo imprimimos en los logs para que sepas QUÉ falló
                print(f"ERROR FECHA: No se pudo convertir '{fecha_str}'. Error: {e}")
                # En caso de error, guardamos la original para no perder el dato, 
                # pero sabrás que está mal si ves '/' en el JSON.
                full_date = fecha_str 

            # Preparamos el objeto para el JSON
            item = {
                'Date': full_date,       # La fecha ya transformada (YYYY-MM-DD)
                'AvgTemp': row['Medias'],
                'Deviation': row['Desviaciones']
            }
            data_list.append(item)
            
        # 4. Guardar como JSON en el bucket procesado
        json_content = json.dumps(data_list)
        # Cambiamos la extensión de .csv a .json
        output_key = key.replace('.csv', '.json')
        
        s3.put_object(Bucket=PROCESSED_BUCKET_NAME, Key=output_key, Body=json_content)
        
        print(f"Exito: JSON guardado en {PROCESSED_BUCKET_NAME}/{output_key}")
        return {'statusCode': 200, 'body': 'Conversion Correcta'}
        
    except Exception as e:
        print(f"ERROR CRITICO: {e}")
        raise e