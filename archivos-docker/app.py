from flask import Flask, request, jsonify
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime, timedelta

app = Flask(__name__)

# IMPORTANTE: Verifica que la región sea la correcta
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('proy-measurements')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

@app.route('/temp', methods=['GET'])
def get_temp():
    month = request.args.get('month')
    year = request.args.get('year')
    if not month or not year:
        return "Faltan parametros", 400

    # Formato de fecha esperado en la BBDD: YYYY-MM
    date_prefix = f"{year}-{month.zfill(2)}"

    response = table.query(
        KeyConditionExpression=Key('LocationId').eq('MarMenor') & Key('Date').begins_with(date_prefix)
    )
    items = response['Items']
    
    if not items:
        return jsonify({"average_temp": 0, "month": month, "year": year})

    # Calcula la media de AvgTemp
    avg_temp = sum(float(i['AvgTemp']) for i in items) / len(items)
    return jsonify({"month": month, "year": year, "average_temp": avg_temp})

@app.route('/sd', methods=['GET'])
def get_sd():
    month = request.args.get('month')
    year = request.args.get('year')
    
    if not month or not year:
        return "Faltan parametros", 400

    date_prefix = f"{year}-{month.zfill(2)}"

    response = table.query(
        KeyConditionExpression=Key('LocationId').eq('MarMenor') & Key('Date').begins_with(date_prefix)
    )
    items = response['Items']
    
    if not items:
        return jsonify({"max_deviation": 0, "month": month, "year": year})

    # Busca la desviación máxima en los items recuperados
    max_sd = max(float(i['Deviation']) for i in items)
    return jsonify({"month": month, "year": year, "max_deviation": max_sd})

@app.route('/maxdiff', methods=['GET'])
def get_maxdiff():
    month = request.args.get('month')
    year = request.args.get('year')
    if not month or not year:
        return "Faltan parametros", 400

    # 1. Calcular fecha mes actual y mes anterior
    current_date = datetime(int(year), int(month), 1)
    # Restamos un dia al dia 1 del mes actual para ir al mes anterior
    prev_date_obj = current_date - timedelta(days=1)
    prev_month = str(prev_date_obj.month).zfill(2)
    prev_year = str(prev_date_obj.year)

    # 2. Consultar Mes Actual
    prefix_curr = f"{year}-{month.zfill(2)}"
    resp_curr = table.query(
        KeyConditionExpression=Key('LocationId').eq('MarMenor') & Key('Date').begins_with(prefix_curr)
    )

    # 3. Consultar Mes Anterior
    prefix_prev = f"{prev_year}-{prev_month}"
    resp_prev = table.query(
        KeyConditionExpression=Key('LocationId').eq('MarMenor') & Key('Date').begins_with(prefix_prev)
    )

    if not resp_curr['Items'] or not resp_prev['Items']:
        return jsonify({"diff": 0, "month": month, "year": year, "error": "Faltan datos"})

    # 4. Buscar Maximos
    max_temp_curr = max(float(i['AvgTemp']) for i in resp_curr['Items'])
    max_temp_prev = max(float(i['AvgTemp']) for i in resp_prev['Items'])

    return jsonify({
        "month": month,
        "year": year,
        "diff": max_temp_curr - max_temp_prev,
        "max_current": max_temp_curr,
        "max_prev": max_temp_prev
    })

@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)