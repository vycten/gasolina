from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# ==============================================================================
# CONFIGURACIÓN DIARIA (Actualiza únicamente si el precio base de la calle cambia)
# ==============================================================================
PRECIOS_ACTUALES_BOMBA = {
    "Súper": 40.60,
    "Regular": 39.60,
    "Diésel": 40.59,
}

# Factores de ajuste (Passthrough FIFO) y desfase logístico en días
FACTOR_PASSTHROUGH = {"Súper": 0.58, "Regular": 0.58, "Diésel": 0.82}
DESFASE_MIN_DIAS = 3
DESFASE_MAX_DIAS = 7

def generar_html():
    try:
        print("Consultando mercados internacionales (NYMEX)...")
        ticker_rbob = yf.Ticker("RB=F")
        ticker_ho = yf.Ticker("HO=F")
        ticker_usdtgq = yf.Ticker("USDGTQ=X")

        df_rbob = ticker_rbob.history(period="1mo")["Close"]
        df_ho = ticker_ho.history(period="1mo")["Close"]
        df_tc = ticker_usdtgq.history(period="1mo")["Close"]

        if df_rbob.empty or df_ho.empty:
            raise ValueError("No se pudieron descargar los datos de mercado.")

        tc_actual = df_tc.iloc[-1] if not df_tc.empty else 7.75

        df_rbob = df_rbob.tail(14)
        df_ho = df_ho.tail(14)

        rbob_semana_ant = df_rbob.iloc[0:7].mean()
        rbob_semana_rec = df_rbob.iloc[7:14].mean()

        ho_semana_ant = df_ho.iloc[0:7].mean()
        ho_semana_rec = df_ho.iloc[7:14].mean()

        diff_rbob_usd = rbob_semana_rec - rbob_semana_ant
        diff_ho_usd = ho_semana_rec - ho_semana_ant

        impacto_gas = diff_rbob_usd * tc_actual * FACTOR_PASSTHROUGH["Súper"]
        impacto_diesel = diff_ho_usd * tc_actual * FACTOR_PASSTHROUGH["Diésel"]

        hoy = datetime.now()
        fecha_limite_ini = hoy + timedelta(days=DESFASE_MIN_DIAS)
        fecha_limite_fin = hoy + timedelta(days=DESFASE_MAX_DIAS)

        lineas = []
        lineas.append("REPORTE DIARIO DE COMBUSTIBLE - GUATEMALA")
        lineas.append(f"Fecha de consulta: {hoy.strftime('%d/%m/%Y')}")
        lineas.append(f"Tipo de cambio:    Q {tc_actual:.2f}")
        lineas.append("-" * 65)

        for prod in ["Súper", "Regular", "Diésel"]:
            precio_hoy = PRECIOS_ACTUALES_BOMBA[prod]
            impacto = impacto_gas if prod in ["Súper", "Regular"] else impacto_diesel
            precio_proyectado = precio_hoy + impacto
            diferencia = precio_proyectado - precio_hoy

            signo = "+" if diferencia >= 0 else ""
            lineas.append(f"{prod:<10} | Actual: Q {precio_hoy:.2f} | Proyectado: Q {precio_proyectado:.2f} | Variación: {signo}Q {diferencia:.2f}")

        lineas.append("-" * 65)
        
        if impacto_gas > 0.15:
            lineas.append("¡ALERTA DE ALZA!")
            lineas.append(f"La gasolina subirá en los siguientes {DESFASE_MIN_DIAS} a {DESFASE_MAX_DIAS} días.")
            lineas.append(f"Ventana de cambio estimada: Del {fecha_limite_ini.strftime('%d/%m/%Y')} al {fecha_limite_fin.strftime('%d/%m/%Y')}.")
            lineas.append(">> RECOMENDACIÓN: Ve a llenar tu tanque HOY antes de que suba el precio.")
        elif impacto_gas < -0.15:
            lineas.append("¡TENDENCIA A LA BAJA!")
            lineas.append(f"Los precios caerán en los siguientes {DESFASE_MIN_DIAS} a {DESFASE_MAX_DIAS} días.")
            lineas.append(f"Ventana de cambio estimada: Del {fecha_limite_ini.strftime('%d/%m/%Y')} al {fecha_limite_fin.strftime('%d/%m/%Y')}.")
            lineas.append(">> RECOMENDACIÓN: Compra solo lo necesario y espera la baja en las gasolineras.")
        else:
            lineas.append("ESTADO: Mercado estable. No se esperan movimientos bruscos en las bombas.")
        lineas.append("=" * 65)

        # Se une fuera del f-string para evitar conflictos con versiones anteriores de Python en el servidor
        contenido_unido = "\n".join(lineas)

        # Contenido HTML con diseño minimalista, texto plano centrado y limpio
        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Combustible Guatemala</title>
    <style>
        body {{
            background-color: #ffffff;
            color: #111111;
            font-family: 'Courier New', Courier, monospace;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            text-align: left;
            font-size: 14px;
            line-height: 1.5;
            background: #fdfdfd;
            padding: 20px;
            border: 1px solid #eaeaea;
            border-radius: 4px;
            max-width: 100%;
        }}
    </style>
</head>
<body>
    <pre>{contenido_unido}</pre>
</body>
</html>
"""

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("index.html generado exitosamente.")

    except Exception as e:
        print(f"Error al procesar el script: {e}")
        error_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Error - Reporte Combustible</title>
    <style>
        body {{ font-family: monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
    </style>
</head>
<body>
    <pre>Error al actualizar los datos de mercado: {e}</pre>
</body>
</html>
"""
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(error_html)

if __name__ == "__main__":
    generar_html()