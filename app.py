from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import urllib.parse
import os

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura_para_doceria'

# Configuração do Banco de Dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///doces.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

NUMERO_WHATSAPP = "5531999999999"


# --- MODELO DO BANCO DE DADOS ---
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(500), nullable=False)


# Cria o banco de dados e insere alguns produtos de exemplo se estiver vazio
with app.app_context():
    db.create_all()
    if not Produto.query.first():
        produtos_iniciais = [
            Produto(nome="Bolo de Pote (Cenoura c/ Chocolate)", preco=12.00,
                    imagem="https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=600&q=80"),
            Produto(nome="Brigadeiro Gourmet (Ao Leite)", preco=4.50,
                    imagem="https://images.unsplash.com/photo-1541783245831-57d6fb0926d3?w=600&q=80")
        ]
        db.session.bulk_save_objects(produtos_iniciais)
        db.session.commit()


# --- FUNÇÕES AUXILIARES ---
def obter_carrinho_detalhado():
    carrinho_sessao = session.get('carrinho', {})
    itens_carrinho = []
    total = 0.0

    for produto_id_str, qtd in carrinho_sessao.items():
        produto = Produto.query.get(int(produto_id_str))
        if produto:
            subtotal = produto.preco * qtd
            total += subtotal
            itens_carrinho.append({
                'id': produto.id,
                'nome': produto.nome,
                'preco': produto.preco,
                'quantidade': qtd,
                'subtotal': subtotal
            })
    return itens_carrinho, total


# --- ROTAS DA LOJA (CLIENTE) ---
@app.route('/')
def index():
    produtos = Produto.query.all()
    itens_carrinho, total = obter_carrinho_detalhado()
    return render_template('index.html', produtos=produtos, carrinho=itens_carrinho, total=total)


@app.route('/adicionar/<int:produto_id>')
def adicionar_ao_carrinho(produto_id):
    carrinho = session.get('carrinho', {})
    id_str = str(produto_id)
    carrinho[id_str] = carrinho.get(id_str, 0) + 1
    session['carrinho'] = carrinho
    return redirect(url_for('index'))


@app.route('/remover/<int:produto_id>')
def remover_do_carrinho(produto_id):
    carrinho = session.get('carrinho', {})
    id_str = str(produto_id)
    if id_str in carrinho:
        if carrinho[id_str] > 1:
            carrinho[id_str] -= 1
        else:
            carrinho.pop(id_str)
    session['carrinho'] = carrinho
    return redirect(url_for('index'))


@app.route('/limpar')
def limpar_carrinho():
    session.pop('carrinho', None)
    return redirect(url_for('index'))


@app.route('/finalizar', methods=['POST'])
def finalizar_pedido():
    nome = request.form.get('nome')
    forma_pagamento = request.form.get('pagamento')
    modo_entrega = request.form.get('entrega')
    endereco = request.form.get('endereco', 'Não informado')

    itens_carrinho, total = obter_carrinho_detalhado()
    if not itens_carrinho:
        return redirect(url_for('index'))

    mensagem = f"🎀 *NOVO PEDIDO - DOCES DA CLARA* 🎀\n\n👤 *Cliente:* {nome}\n🚚 *Entrega:* {modo_entrega}\n"
    if modo_entrega == 'Entrega':
        mensagem += f"📍 *Endereço:* {endereco}\n"
    mensagem += f"💳 *Pagamento:* {forma_pagamento}\n\n🛒 *Resumo do Pedido:*\n"

    for item in itens_carrinho:
        mensagem += f"• {item['quantidade']}x {item['nome']} (R$ {item['preco']:.2f})\n"

    mensagem += f"\n💰 *Total:* R$ {total:.2f}"

    session.pop('carrinho', None)
    return redirect(f"https://api.whatsapp.com/send?phone={NUMERO_WHATSAPP}&text={urllib.parse.quote(mensagem)}")


# --- ROTAS DO ADMIN (GERENCIAMENTO) ---
@app.route('/admin')
def admin():
    produtos = Produto.query.all()
    return render_template('admin.html', produtos=produtos)


@app.route('/admin/adicionar', methods=['POST'])
def admin_adicionar():
    nome = request.form.get('nome')
    preco = float(request.form.get('preco').replace(',', '.'))
    imagem = request.form.get('imagem')

    novo_produto = Produto(nome=nome, preco=preco, imagem=imagem)
    db.session.add(novo_produto)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin/excluir/<int:produto_id>')
def admin_excluir(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    db.session.delete(produto)
    db.session.commit()

    # Remove do carrinho se alguém estiver comprando
    carrinho = session.get('carrinho', {})
    if str(produto_id) in carrinho:
        carrinho.pop(str(produto_id))
        session['carrinho'] = carrinho

    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)