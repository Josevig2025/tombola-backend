
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import pandas as pd
from io import BytesIO
from collections import Counter
from itertools import combinations

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def read_ods(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes), engine="odf", header=None)
    data = df.dropna(how='all').values.tolist()[1:]  # omitir encabezado si lo hay
    return data

def analizar_combinaciones(data, cantidad):
    conteo = Counter()
    for fila in data:
        numeros = [int(n) for n in fila if isinstance(n, (int, float))]
        for combo in combinations(sorted(numeros), cantidad):
            conteo[combo] += 1
    return conteo

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    content = await file.read()
    data = read_ods(content)

    resultados = {}
    for n in range(3, 8):
        conteo = analizar_combinaciones(data, n)
        mas_frecuentes = conteo.most_common(10)
        menos_frecuentes = sorted(
            ((k, sum(1 for fila in data if set(k).issubset(set(fila))) or 0)
             for k in conteo),
            key=lambda x: x[1]
        )[:10]

        resultados[f"{n}"] = {
            "frequent": [{"combo": list(k), "count": v} for k, v in mas_frecuentes],
            "delayed": [{"combo": list(k), "delay": v} for k, v in menos_frecuentes]
        }

    return JSONResponse(content=resultados)
