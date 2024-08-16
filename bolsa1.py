import streamlit as st
import yfinance as yfin
import pandas as pd
import plotly.graph_objs as go
import mplfinance as mpl
from prophet import Prophet

st.set_page_config( 
    page_title="Gráfico de Ações",
    layout="centered"
)
st.header('HISTORICO DE VALOR DAS AÇÕES')

@st.cache_data
def carrega_dados(acao):
    base = yfin.Ticker(acao)
    base = pd.DataFrame(base.history(period="1d", start="2023-01-01", end=None))
    base.index = pd.to_datetime(base.index)
    for i in base.columns:
        base[i] = base[i].astype(float)
    return base

ticker = st.text_input('Digite o código de sua ação: ')
base = carrega_dados(f'{ticker}.SA')

st.title('Gráfico de Candles com Médias Móveis')
fig , ax =  mpl.plot(
            base, #base de dados a ser exibida, deve conter datas como indice, e valores de abertura, fechamento, maxima e minima
            type = 'candle', #tipo de gráfico ()
            title=ticker,
            figsize = (15,9),  #tamanho da imagem
            volume = False,  #imprimir volume
            mav = (10, 20),  #médias móveis
            style = 'yahoo',#estilo print(mpf.available_styles())
            returnfig=True) 
st.pyplot(fig)


st.write('Previsão de 30 dias com o Prophet do FAcebook')

@st.cache_data
def dados_fb(base):
    #quando for trabalhar com o Prophet o FB, precisa renomear as colunas para ds e y (padrão da bib)
    base = base.reset_index()
    dadosfb = base[['Date', 'Close']].rename(columns={'Date':'ds','Close':'y'})
    #removendo timezone
    dadosfb['ds'] = pd.to_datetime(dadosfb['ds'])
    dadosfb['ds'] = dadosfb['ds'].dt.tz_localize(None)
    return dadosfb

basefb = dados_fb(base)
modelo = Prophet()
modelo.fit(basefb)
futuro = modelo.make_future_dataframe(periods=30)
previsoes = modelo.predict(futuro)
fig = modelo.plot(previsoes, xlabel = 'Data', ylabel = 'Preço');
st.pyplot(fig,)

st.plotly_chart(fig,on_select='rerun',selection_mode='box', theme='streamlit')

st.write(' # Fim do App  ')