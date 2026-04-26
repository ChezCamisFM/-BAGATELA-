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
