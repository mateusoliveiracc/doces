from flask import Flask, render_template, request, redirect, url_for, session
import urllib.parse

app = Flask(__name__)
app.secret_key = 'chave_secreta_super_segura_para_doceria'

# Substitua pelo número do WhatsApp do vendedor (com DDD, apenas números)
# Exemplo: 5531999999999
NUMERO_WHATSAPP = "31990641603"

# Simulação de um banco de dados de produtos
PRODUTOS = [
    {
        "id": 1,
        "nome": "Bolo de Pote (Cenoura com Chocolate)",
        "preco": 12.00,
        "imagem": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500"
    },
    {
        "id": 2,
        "nome": "Brigadeiro Gourmet (Unidade)",
        "preco": 4.50,
        "imagem": "https://images.unsplash.com/photo-1541783245831-57d6fb0926d3?w=500"
    },
    {
        "id": 3,
        "nome": "Brownie Tradicional",
        "preco": 8.00,
        "imagem": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=500"
    },
    {
        "id": 4,
        "nome": "Copo da Felicidade (Morango e Ninho)",
        "preco": 16.00,
        "imagem": "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=500"
    }
]


def obter_carrinho_detalhado():
    """Função auxiliar para cruzar os IDs da sessão com os dados dos produtos"""
    carrinho_sessao = session.get('carrinho', {})
    itens_carrinho = []
    total = 0.0

    for produto_id_str, qtd in carrinho_sessao.items():
        prod_id = int(produto_id_str)
        produto = next((p for p in PRODUTOS if p['id'] == prod_id), None)
        if produto:
            subtotal = produto['preco'] * qtd
            total += subtotal
            itens_carrinho.append({
                'id': produto['id'],
                'nome': produto['nome'],
                'preco': produto['preco'],
                'quantidade': qtd,
                'subtotal': subtotal
            })
    return itens_carrinho, total


@app.route('/')
def index():
    itens_carrinho, total = obter_carrinho_detalhado()
    return render_template('index.html', produtos=PRODUTOS, carrinho=itens_carrinho, total=total)


@app.route('/adicionar/<int:produto_id>')
def adicionar_ao_carrinho(produto_id):
    if 'carrinho' not in session:
        session['carrinho'] = {}

    carrinho = session['carrinho']
    id_str = str(produto_id)

    if id_str in carrinho:
        carrinho[id_str] += 1
    else:
        carrinho[id_str] = 1

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

    # Construção do texto formatado para o WhatsApp
    mensagem = f"🧁 *NOVO PEDIDO RECEBIDO!* 🧁\n\n"
    mensagem += f"👤 *Cliente:* {nome}\n"
    mensagem += f"🚚 *Modo de Entrega:* {modo_entrega}\n"
    if modo_entrega == 'Entrega':
        mensagem += f"📍 *Endereço:* {endereco}\n"
    mensagem += f"💳 *Forma de Pagamento:* {forma_pagamento}\n\n"
    mensagem += f"🛒 *Itens do Pedido:*\n"

    for item in itens_carrinho:
        mensagem += f"• {item['quantidade']}x {item['nome']} (R$ {item['preco']:.2f} cada)\n"

    mensagem += f"\n💰 *Total Geral:* R$ {total:.2f}"

    # Codifica o texto para o formato aceito em URLs
    mensagem_codificada = urllib.parse.quote(mensagem)

    # Limpa o carrinho após finalizar
    session.pop('carrinho', None)

    # URL final para redirecionamento
    whatsapp_url = f"https://api.whatsapp.com/send?phone={NUMERO_WHATSAPP}&text={mensagem_codificada}"

    return redirect(whatsapp_url)


if __name__ == '__main__':
    app.run(debug=True)