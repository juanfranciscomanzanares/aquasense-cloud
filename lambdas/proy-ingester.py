import json
import boto3
from decimal import Decimal
from datetime import datetime
import statistics

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

TABLE_NAME = 'proy-measurements'
ALARM_FUNCTION_NAME = 'proy-alarm-worker'

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)
    
    # 1. Obtener bucket y archivo
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    print(f"Iniciando carga optimizada para: {key}")
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        json_content = response['Body'].read().decode('utf-8')
        data = json.loads(json_content, parse_float=Decimal)
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
        raise e

    weeks_data = {}
    weeks_details = {}

    # Esto abre un gestor de contexto que agrupa escrituras automáticamente
    with table.batch_writer() as batch:
        for item in data:
            try:
                # A. Guardar en DynamoDB (En lote, mucho más rápido)
                db_item = {
                    'LocationId': 'MarMenor', 
                    'Date': item['Date'],
                    'AvgTemp': item['AvgTemp'],
                    'Deviation': item['Deviation']
                }
                batch.put_item(Item=db_item)
                
                # B. Lógica de Agrupación (En memoria)
                dt = datetime.strptime(item['Date'], '%Y-%m-%d')
                year, week_num, _ = dt.isocalendar()
                week_key = f"{year}-W{week_num}" 
                
                if week_key not in weeks_data:
                    weeks_data[week_key] = []
                    weeks_details[week_key] = []
                
                temp_val = float(item['AvgTemp'])
                weeks_data[week_key].append(temp_val)
                
                weeks_details[week_key].append({
                    'date': item['Date'],
                    'temp': temp_val
                })
                
            except Exception as e:
                print(f"Error procesando registro {item}: {e}")
                continue

    print("Escritura en DynamoDB completada. Analizando alertas...")

    # --- PASO 2: Cálculo y Alertas ---
    alerts_sent = 0
    for week_key, temps in weeks_data.items():
        # Se necesitan al menos 2 datos para desviación estándar
        if len(temps) < 2:
            continue
            
        calculated_sd = statistics.stdev(temps)
        
        if calculated_sd > 0.5:
            print(f">> ALERTA SEMANA {week_key}: SD {calculated_sd:.4f}")
            
            payload = {
                'week_id': week_key,
                'calculated_sd': round(calculated_sd, 4),
                'measurements_count': len(temps),
                'daily_data': weeks_details[week_key]
            }
            
            lambda_client.invoke(
                FunctionName=ALARM_FUNCTION_NAME,
                InvocationType='Event',
                Payload=json.dumps(payload)
            )
            alerts_sent += 1

    return {
        'statusCode': 200, 
        'body': f'Proceso fin. Registros: {len(data)}. Alertas enviadas: {alerts_sent}'
    }