import json
import boto3

sns = boto3.client('sns')

# Sustituye con tu ARN real
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:684973592846:proy-alarm-topic'

def lambda_handler(event, context):
    # Recuperar datos del evento semanal
    week_id = event.get('week_id', 'Desconocida')
    sd_val = event.get('calculated_sd', 0.0)
    count = event.get('measurements_count', 0)
    daily_data = event.get('daily_data', [])
    
    # Construir Asunto
    subject = f"ALERTA SEMANAL MAR MENOR: Semana {week_id}"
    
    # Construir Cuerpo del Mensaje
    message = f"ALERTA DE DESVIACIÓN DE TEMPERATURA\n"
    message += f"===================================\n"
    message += f"Semana: {week_id}\n"
    message += f"Desviación Estándar Calculada: {sd_val} (Umbral: 0.5)\n"
    message += f"Número de mediciones procesadas: {count}\n\n"
    
    message += "Desglose de mediciones utilizadas:\n"
    message += "-----------------------------------\n"
    for day in daily_data:
        message += f" - {day['date']}: {day['temp']} °C\n"
        
    print(f"Enviando correo para semana {week_id}...")
    
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject=subject
        )
    except Exception as e:
        print(f"Error SNS: {e}")
        raise e
        
    return {'statusCode': 200, 'body': 'Alerta semanal enviada'}