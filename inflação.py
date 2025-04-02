import requests
import pandas as pd


url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"


params = {
    "formato": "json",
    "dataInicial": "01/01/2000",
    "dataFinal": "31/12/2024"
}
q=[]
c=1.0
try:
    
    response = requests.get(url, params=params)
    response.raise_for_status()

    
    data = response.json()

    if not data:
        print("Nenhum dado encontrado.")
    else:
        
        df = pd.DataFrame(data)
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
        df['valor'] = df['valor'].astype(float)

        
        df['ano'] = df['data'].dt.year

        
        inflacao_anual = df.groupby('ano')['valor'].sum().reset_index()

       
        array_inflacao = inflacao_anual.values.tolist()

        
        print("Inflação ano a ano:")
        for ano, inflacao in array_inflacao:
            print(inflacao,' ',end='')
            

except requests.RequestException as e:
    print(f"Erro ao fazer a requisição: {e}")
except Exception as e:
    print(f"Erro inesperado: {e}")
