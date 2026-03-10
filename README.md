# 🌊 AquaSenseCloud — Monitorización Ambiental del Mar Menor con AWS

<p align="center">
  <img src="https://img.shields.io/badge/AWS-Cloud-orange?logo=amazonaws" />
  <img src="https://img.shields.io/badge/Python-3.9-blue?logo=python" />
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker" />
  <img src="https://img.shields.io/badge/IaC-CloudFormation-blueviolet" />
</p>

Plataforma serverless en AWS para la **ingesta, procesamiento y consulta en tiempo real** de datos de temperatura del Mar Menor (Murcia), con un sistema de **alertas automáticas** ante desviaciones térmicas anómalas.

> Proyecto final de la asignatura **Infraestructura y Computación de Altas Prestaciones (ICAP)** — Universidad de Murcia, Grado en Ingeniería Informática.

---

## 📐 Arquitectura

El sistema sigue una arquitectura **event-driven serverless** compuesta por tres pipelines diferenciados:

```
                        ┌────────────────────────────┐
  CSV Upload ──►  S3 (raw)  ──► Lambda Converter ──► S3 (processed JSON)
                        └────────────────────────────┘
                                                          │
                                                          ▼
                                              Lambda Ingester
                                              ┌──────────────┐
                                              │ Batch Write   │──► DynamoDB
                                              │ Alarm Logic   │──► Lambda Alarm Worker ──► SNS (email)
                                              └──────────────┘
                                                          
  User ──► ALB ──► ECS (Flask API in Docker) ──► DynamoDB
```

| Pipeline | Descripción |
|----------|------------|
| **Ingesta** | Los CSVs se suben a S3, se convierten a JSON y se cargan por lotes en DynamoDB |
| **Alertas** | Si la desviación estándar semanal supera un umbral (0.5 °C), se envía un email vía SNS |
| **Consulta** | Una API REST (Flask) desplegada en ECS con Docker permite consultar temperaturas medias, desviaciones y diferencias entre meses |

---

## 🧩 Componentes

### AWS Lambda Functions

| Función | Archivo | Rol |
|---------|---------|-----|
| **Converter** | [`proy-converter.py`](lambdas/proy-converter.py) | Convierte CSV → JSON, normaliza fechas y lo deposita en el bucket procesado |
| **Ingester** | [`proy-ingester.py`](lambdas/proy-ingester.py) | Carga JSON en DynamoDB (batch write), calcula SD semanal e invoca alarmas |
| **Alarm Worker** | [`proy-alarm-worker.py`](lambdas/proy-alarm-worker.py) | Publica alertas detalladas en un topic SNS con desglose diario |

### API REST (Flask + Docker + ECS)

Flask app contenedorizada que expone:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/temp?month=MM&year=YYYY` | GET | Temperatura media del mes |
| `/sd?month=MM&year=YYYY` | GET | Desviación máxima del mes |
| `/maxdiff?month=MM&year=YYYY` | GET | Diferencia de máximos entre mes actual y anterior |
| `/health` | GET | Health check |

### Infraestructura como Código (CloudFormation)

[`proy-red-base.yaml`](automatizacion/proy-red-base.yaml) despliega la infraestructura de red completa:

- **VPC** con 2 subredes públicas + 2 privadas (multi-AZ)
- **NAT Gateway** para salida a Internet desde subredes privadas
- **Security Groups** segmentados (ALB ↔ Contenedores)
- Internet Gateway, tablas de rutas y asociaciones

---

## 🗂️ Estructura del repositorio

```
.
├── archivos-docker/
│   ├── Dockerfile              # Imagen Docker para la API Flask
│   ├── app.py                  # API REST Flask
│   └── requirements.txt        # Dependencias Python (flask, boto3)
├── lambdas/
│   ├── proy-converter.py       # Lambda: CSV → JSON
│   ├── proy-ingester.py        # Lambda: Carga en DynamoDB + alertas
│   └── proy-alarm-worker.py    # Lambda: Envío de alertas por SNS
├── automatizacion/
│   └── proy-red-base.yaml      # CloudFormation: infraestructura de red
├── CSVs/
│   ├── Temperatura.csv         # Dataset original de temperaturas
│   ├── datos_parte_*.csv       # Fragmentos para simular carga incremental
│   └── split_data.py           # Script para dividir el CSV en partes
├── Memoria_Proyecto_ICAP.pdf   # 📄 Memoria completa del proyecto
└── README.md
```

---

## 🛠️ Servicios AWS utilizados

| Servicio | Uso |
|----------|-----|
| **S3** | Almacenamiento de CSVs (raw) y JSONs (procesados) |
| **Lambda** | Procesamiento serverless (conversión, ingesta, alertas) |
| **DynamoDB** | Base de datos NoSQL para mediciones |
| **SNS** | Notificaciones por email ante anomalías |
| **ECS + Fargate** | Ejecución de contenedores Docker |
| **ECR** | Registro de imágenes Docker |
| **ALB** | Balanceador de carga para la API |
| **CloudFormation** | Infraestructura como código |
| **VPC** | Red virtual con subredes públicas/privadas |

---

## 🚀 Despliegue

### 1. Infraestructura de red
```bash
aws cloudformation deploy \
  --template-file automatizacion/proy-red-base.yaml \
  --stack-name proy-red-base
```

### 2. Imagen Docker
```bash
cd archivos-docker
docker build -t proy-api .
# Push a ECR y desplegar en ECS
```

### 3. Lambdas
Subir cada archivo `.py` de `lambdas/` como función Lambda, configurando los triggers S3 correspondientes.

---

## 📊 Dataset

Datos reales de temperatura del Mar Menor. El script `CSVs/split_data.py` divide el dataset original en 3 partes para simular la carga incremental de datos en el pipeline.

---

## 📝 Memoria

La memoria completa del proyecto se encuentra en [`Memoria_Proyecto_ICAP.pdf`](Memoria_Proyecto_ICAP.pdf), donde se detalla el diseño, implementación, pruebas y conclusiones.

---

## 👤 Autor

Proyecto desarrollado para la asignatura de **ICAP** — Universidad de Murcia (2025-2026).
