from flask import Flask, render_template, request, jsonify
import re
from graphviz import Digraph

app = Flask(__name__)

class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

def lexical_analyzer(expression):
    # Expresiones regulares para identificar números, operadores y paréntesis
    regex_patterns = [
        (r'\d+\.?\d*', 'NUMERO'),
        (r'\+', 'SUMA'),
        (r'\-', 'RESTA'),
        (r'\*', 'MULTIPLICACION'),
        (r'\/', 'DIVISION'),
        (r'\(', 'PARENTIZQ'),
        (r'\)', 'PARENTDER'),
    ]
    
    tokens = []
    position = 0
    
    while position < len(expression):
        match = None
        for pattern, token_type in regex_patterns:
            regex = re.compile(pattern)
            match = regex.match(expression, position)
            if match:
                value = match.group(0)
                tokens.append({'value': value, 'type': token_type, 'position': position})
                position = match.end()
                break
        if not match:
            raise ValueError('Invalid character at position ' + str(position))
            
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0

    def parse(self):
        root = self.expression()
        if self.current_token_index < len(self.tokens):
            raise ValueError('Unexpected token at position ' + str(self.current_token_index))
        return root

    def expression(self):
        node = self.term()
        while self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            if token['type'] in ['SUMA', 'RESTA']:
                self.current_token_index += 1
                operator = Node(token['value'])
                operator.left = node
                operator.right = self.term()
                node = operator
            else:
                break
        return node

    def term(self):
        node = self.factor()
        while self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            if token['type'] in ['MULTIPLICACION', 'DIVISION']:
                self.current_token_index += 1
                operator = Node(token['value'])
                operator.left = node
                operator.right = self.factor()
                node = operator
            else:
                break
        return node

    def factor(self):
        token = self.tokens[self.current_token_index]
        if token['type'] == 'NUMERO':
            self.current_token_index += 1
            return Node(token['value'])
        elif token['type'] == 'PARENTIZQ':
            self.current_token_index += 1
            node = self.expression()
            if self.tokens[self.current_token_index]['type'] != 'PARENTDER':
                raise ValueError('Missing closing parenthesis')
            self.current_token_index += 1
            return node
        else:
            raise ValueError('Unexpected token at position ' + str(self.current_token_index))

def build_tree(tokens):
    parser = Parser(tokens)
    return parser.parse()

def print_tree(node, graph, parent=None):
    if node is not None:
        graph.node(str(node), node.value)
        if parent is not None:
            graph.edge(str(parent), str(node))
        print_tree(node.left, graph, node)
        print_tree(node.right, graph, node)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    expression = request.form['expression']
    try:
        # Realiza el análisis léxico
        tokens = lexical_analyzer(expression)
        # Construye el árbol de derivación
        root = build_tree(tokens)
        # Crea un objeto Digraph para el árbol
        graph = Digraph(comment='Expression Tree')
        # Imprime el árbol en el objeto Digraph
        print_tree(root, graph)
        # Guarda el árbol como imagen
        graph.render('static/expression_tree', format='png', cleanup=True)
        # Evalúa la expresión
        result = evaluate_expression(expression)
        return jsonify({'result': result, 'tokens': tokens})
    except ValueError as e:
        return jsonify({'error': str(e)})

def evaluate_expression(expression):
    # Evalúa la expresión matemática
    return eval(expression)

if __name__ == '__main__':
    app.run(debug=True)
