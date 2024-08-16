#https://github.com/codigoquant/stock_dashboard

import requests,  streamlit as st, pandas as pd, numpy as np, yfinance as yf, mplfinance as mpl, plotly.express as px
from streamlit_extras.grid import grid
from datetime import datetime
from prophet import Prophet
from datetime import timedelta as td
from datetime import date

#from b3fileparser.b3parser import B3Parser
#parser = B3Parser.create_parser(engine='pandas')
#dados_b3 = parser.read_b3_file('COTAHIST_A2024.TXT')
#pegando dados das PUTS da Petro
#puts = dados[dados['TIPO_DE_MERCADO'] == 'OPCOES_DE_VENDA']
#putspetro = puts[puts['CODIGO_DE_NEGOCIACAO'].str.startswith('PETR')]
#putspetro.head()

#pegando dados de API
#pegar dados das opções https://www.dadosdemercado.com.br/acoes
#'https://br.advfn.com/common/bov-options/api?symbol=BBAS3&_=1723247669644'

def pega_opcoes(acao = 'BBAS3'):
    URL = 'https://br.advfn.com/common/bov-options/api'

    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
    'Accept': '*/*', 'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
    'X-Requested-With': 'XMLHttpRequest', 'DNT': '1',
    'Connection': 'keep-alive', 'Sec-Fetch-Dest': 'empty','Sec-Fetch-Mode': 'cors','Sec-Fetch-Site': 'same-origin',
    }

    params = {'symbol': acao, }
    #executando a query
    response = requests.get(URL, params=params, headers=headers)
    #converteno para um formato de dataframe
    dictr = response.json()
    df = pd.json_normalize(dictr['result'])
    df['url'] ='https://br.advfn.com'+df['url'].values
    return df

st.set_page_config(page_title="Gráfico de Ações", layout="wide")
st.title('HISTORICO DE VALOR DAS AÇÕES')

@st.cache_data
def carrega_dados(acao='PETR4', inicio='2022-01-01', fim=None):
    base = yf.Ticker(acao)
    base = pd.DataFrame(base.history(period="1d", start=inicio, end=fim))
    base.index = pd.to_datetime(base.index)
    for i in base.columns:
        base[i] = base[i].astype(float)
    return base

@st.cache_data
def dados_fb(base):
    #quando for trabalhar com o Prophet o FB, precisa renomear as colunas para ds e y (padrão da bib)
    base = base.reset_index()
    dadosfb = base[['Date', 'Close']].rename(columns={'Date':'ds','Close':'y'})
    #removendo timezone
    dadosfb['ds'] = pd.to_datetime(dadosfb['ds'])
    dadosfb['ds'] = dadosfb['ds'].dt.tz_localize(None)
    modelo = Prophet()
    modelo.fit(dadosfb)
    futuro = modelo.make_future_dataframe(periods=30)
    previsoes = modelo.predict(futuro)
    fig = modelo.plot(previsoes, xlabel = 'Data', ylabel = 'Preço');
    st.pyplot(fig)

with st.sidebar:
    ticker_list = pd.read_csv("tickers.csv", index_col=0)
    ticker = st.selectbox(label="Selecione a Acao", options=ticker_list, placeholder='Códigos')
    base_t = carrega_dados(ticker+".SA")
    datamin = base_t.index.min().to_pydatetime()
    datamax = base_t.index.max().to_pydatetime()
    intervalo = st.slider("Selecione o período", min_value=datamin, max_value=datamax, value=(datamin, datamax), step=td(days=5))
    base = base_t.loc[intervalo[0]:intervalo[1]]
    if ticker is not None:
        opcoes = pega_opcoes(ticker)
        seletor = st.radio('Tipo', ['Call', 'Put'], index=None)
        op = opcoes[opcoes['type'] == seletor].sort_values(by=['expiry_date', 'strike_price'])
        options = st.sidebar.multiselect(label="Selecione as opçoes", options=op['symbol'], placeholder='Códigos')         


col1, col2 = st.columns(2, gap='large')
with col1:
    st.subheader("Gráfico de Candles")
    fig,ax = mpl.plot(base.tail(30), type='candle', volume = False, mav = (10, 20),style = 'yahoo', returnfig=True) 
    st.pyplot(fig)

with col2:
    st.subheader("Previsão Com Prophet")
    dados_fb(base_t)
    st.dataframe(op.loc[op['symbol'].isin(options)])