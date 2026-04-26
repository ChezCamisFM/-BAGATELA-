# BAGATELA SCRAPER 2026 (Phyton + Playright) 
BAGATELA é o protótipo de scraper assíncrono usando Flask (Backend) e BeautifulSoup (Extração de Dados) com o MVP inicialmente focado na coleta de dados B2C para Mercado Livre (Brasil), Amazon (Brasil) e Shopee, de forma resiliente, modular e escalável. 

# Project Description 

Criar um app para comparar preço de um mesmo produto no Mercado Livre, Shopee e Amazon Brasil. 
Salva os dados : 
Em um arquivo JSON
Em uma captura de tela (screenshot)
Em um arquivo HTML bruto da página

# Structure 

comparador_precos/
├── app.py
├── scraper.py
├── templates/
│   └── index.html
└── requirements.txt

# Requirements.txt

Flask==3.0.0
playwright==1.40.0

# After installing, run on terminal to download browsers

playwright install chromium

# Scraper.py

import asyncio
from playwright.async_api import async_playwright

async def get_price_mercadolivre(page, produto):
    url = f"https://lista.mercadolivre.com.br/{produto.replace(' ', '-')}"
    await page.goto(url, wait_until='domcontentloaded')
    # O Mercado Livre carrega o preço no HTML estático
    preco_element = await page.query_selector('.andes-money-amount__fraction')
    if preco_element:
        texto = await preco_element.inner_text()
        preco = texto.replace('.', '').replace(',', '.')
        return float(preco)
    return None

async def get_price_amazon(page, produto):
    url = f"https://www.amazon.com.br/s?k={produto.replace(' ', '+')}"
    await page.goto(url, wait_until='domcontentloaded')
    # Amazon usa classe .a-price-whole (pode demorar um pouco)
    try:
        await page.wait_for_selector('.a-price-whole', timeout=5000)
        preco_element = await page.query_selector('.a-price-whole')
        if preco_element:
            texto = await preco_element.inner_text()
            preco = texto.replace('.', '').replace(',', '')
            return float(preco)
    except:
        return None
    return None

async def get_price_shopee(page, produto):
    url = f"https://shopee.com.br/search?keyword={produto.replace(' ', '%20')}"
    await page.goto(url, wait_until='networkidle')  # espera JS carregar
    # A Shopee carrega preços dentro de div com classe específica
    try:
        await page.wait_for_selector('[class*="ZEgDH9"]', timeout=8000)
        preco_element = await page.query_selector('[class*="ZEgDH9"]')
        if preco_element:
            texto = await preco_element.inner_text()
            # extrai primeiro número (ex: "R$ 1.299,00" -> 1299.00)
            import re
            match = re.search(r'[\d\.]+,\d{2}', texto.replace('.', ''))
            if match:
                preco = match.group().replace(',', '.')
                return float(preco)
    except:
        return None
    return None

async def comparar_precos_async(produto):
    async with async_playwright() as p:
        # Lança navegador Chromium (headless = sem interface gráfica)
        browser = await p.chromium.launch(headless=True)
        # Cria uma nova aba (contexto) para cada loja, para isolar cookies
        context = await browser.new_context()
        
        ml_page = await context.new_page()
        amz_page = await context.new_page()
        shp_page = await context.new_page()
        
        # Executa as três buscas em paralelo
        ml_task = get_price_mercadolivre(ml_page, produto)
        amz_task = get_price_amazon(amz_page, produto)
        shp_task = get_price_shopee(shp_page, produto)
        
        ml_price, amz_price, shp_price = await asyncio.gather(ml_task, amz_task, shp_task)
        
        await browser.close()
        return {
            'Mercado Livre': ml_price,
            'Amazon': amz_price,
            'Shopee': shp_price
        }

# Função síncrona para ser chamada pelo Flask
def comparar_precos(produto):
    return asyncio.run(comparar_precos_async(produto))

 # app.py

from flask import Flask, request, render_template
from scraper import comparar_precos

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    resultados = None
    produto_buscado = ''
    if request.method == 'POST':
        produto_buscado = request.form['produto']
        resultados = comparar_precos(produto_buscado)
    return render_template('index.html', resultados=resultados, produto=produto_buscado)

if __name__ == '__main__':
    app.run(debug=True)

# templates/index.html

<!DOCTYPE html>
<html>
<head>
    <title>Comparador de Preços</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; text-align: center; }
        input, button { padding: 10px; font-size: 16px; margin: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 10px; }
        th { background: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Comparador de Preços</h1>
    <form method="POST">
        <input type="text" name="produto" placeholder="Ex: iPhone 13" value="{{ produto }}" required>
        <button type="submit">Comparar</button>
    </form>

    {% if resultados %}
    <table>
        <tr><th>Plataforma</th><th>Preço (R$)</th></tr>
        <tr><td>Mercado Livre</td><td>{{ resultados['Mercado Livre'] or 'Não encontrado' }}</td></tr>
        <tr><td>Amazon</td><td>{{ resultados['Amazon'] or 'Não encontrado' }}</td></tr>
        <tr><td>Shopee</td><td>{{ resultados['Shopee'] or 'Não encontrado' }}</td></tr>
    </table>
    {% endif %}
</body>
</html>

# How to run : 
pip install -r requirements.txt
playwright install chromium
python app.py
