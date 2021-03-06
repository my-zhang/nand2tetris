
import sys
from jcompiler.token import token_stream
from jcompiler.token import token_type

class Parser(object): 
    '''parsing phase of frontend''' 

    def __init__(self, tokens): 
        self.buf = token_stream(tokens) 
        self.lookahead = self.buf.next() 

    def match(self, t): 
        if t is not None and t != self.lookahead: 
            raise ValueError(
                    '[ERROR] "%s" is expected, while the buf is "%s".' 
                    %(t, self.lookahead)) 
        self.lookahead = self.buf.next() 

    def parse_tree(self): 
        '''return a parse tree by analyzing the input tokens'''
        return self.klass() 

    def klass(self): 
        if self.lookahead == 'class': 
            return ['class', self.keyword(), self.class_name(), 
                    self.symbol()] + self.class_vars() + \
                    self.subroutines() + [self.symbol()] 

    def keyword(self, k=None): 
        t = self.lookahead 
        self.match(k) 
        return ['keyword', t]

    def identifier(self): 
        t = self.lookahead
        self.match(t) 
        return ['identifier', t] 

    def symbol(self, s=None): 
        t = self.lookahead 
        self.match(s) 
        return ['symbol', t] 

    def class_vars(self): 
        if self.lookahead not in ['static', 'field']: 
            return []
        return [['classVarDec', self.keyword(), self.data_type(), 
            self.var_name()] + self.var_names() + [self.symbol()]] + \
            self.class_vars()

    def data_type(self): 
        if self.lookahead in ['int', 'char', 'boolean']: 
            return self.keyword() 
        else: 
            return self.identifier() 

    def class_name(self): 
        return self.identifier() 

    def var_dec(self): 
        node = ['varDec', self.symbol('var'), self.data_type(), 
                self.var_name()] 
        while self.lookahead == ',': 
            node += [self.symbol(','), self.var_name()] 
        return node + [self.symbol(';')] 

    def var_name(self): 
        return self.identifier() 

    def subroutine_name(self): 
        return self.identifier() 

    def var_names(self): 
        '''zero or more var names'''
        t = self.lookahead
        if t == ',': 
            return [self.symbol(), self.var_name()] + self.var_names()
        else: 
            return [] 

    def subroutines(self): 
        if self.lookahead not in ['constructor', 'function', 'method']: 
            return [] 
        return [['subroutineDec', self.keyword(), self.ret_type(), 
            self.subroutine_name(), self.symbol(), self.para_list(), 
            self.symbol(), self.subroutine_body()]] + self.subroutines() 

    def ret_type(self): 
        if self.lookahead == 'void': 
            return self.keyword() 
        return self.data_type() 

    def para_list(self): 
        if self.lookahead == ')': 
            return ['parameterList', []] 

        node = ['parameterList', self.data_type(), self.var_name()] 

        while self.lookahead == ',': 
            node += [self.symbol(), self.data_type(), self.var_name()] 

        return node

    def subroutine_body(self): 
        node = ['subroutineBody', self.symbol()] 
        while self.lookahead == 'var': 
            node += [self.var_dec()] 

        node += [self.statements(), self.symbol()] 
        return node 

    def statements(self): 
        node = ['statements'] 
        while self.lookahead in ['let', 'if', 'while', 'do', 'return']: 
            node += [self.statement()] 
        return node 

    def statement(self): 
        t = self.lookahead
        if t == 'let': 
            return self.let_stmt() 
        elif t == 'if': 
            return self.if_stmt() 
        elif t == 'while': 
            return self.while_stmt() 
        elif t == 'do': 
            return self.do_stmt() 
        elif t == 'return': 
            return self.ret_stmt() 
        else: 
            pass 

    def let_stmt(self): 
        node =  ['letStatement', self.keyword('let'), self.var_name()] 
        if self.lookahead != '=': 
            node += [self.symbol('['), self.expression(), self. symbol(']')] 
        node += [self.symbol('='), self.expression(), self.symbol(';')] 
        return node

    def if_stmt(self): 
        node =  ['ifStatement', self.keyword('if'), self.symbol('('), 
                self.expression(), self.symbol(')'), self.symbol('{'), 
                self.statements(), self.symbol('}')] 
        if self.lookahead == 'else': 
            node += [self.keyword('else'), self.symbol('{'), 
                        self.statements(), self.symbol('}')] 
        return node 

    def while_stmt(self): 
        return ['whileStatement', self.keyword('while'), self.symbol(), 
                self.expression(), self.symbol(), self.symbol(), 
                self.statements(), self.symbol()] 

    def do_stmt(self): 
        return  ['doStatement', self.keyword('do'), 
                 self.identifier()] + self.subroutine_call()

    def ret_stmt(self): 
        node = ['returnStatement', self.keyword('return')] 
        if self.lookahead != ';': 
            node += [self.expression()] 
        else: 
            node += [self.symbol(';')] 
        return node 

    def subroutine_call(self): 
        'code after the class name or func name' 
        node = []
        if self.lookahead == '.': 
            node += [self.symbol('.'), self.identifier()] 
        node += [self.symbol('('), self.expr_list(), self.symbol(')')] 
        return node 

    def expression(self): 
        node = ['expression', self.term()]
        while self.lookahead in '+-*/&|<>=': 
            node += [self.op(), self.term()] 
        return node 

    def term(self): 
        t = self.lookahead; 
        node = ['term']
        if token_type(t) == 'keyword': 
            return node + [self.keyword()] 
        elif token_type(t) == 'integerConstant': 
            return node + [self.int_const()] 
        elif token_type(t) == 'stringConstant': 
            return node + [self.str_const()] 
        elif t == '(': 
            return node + [self.symbol(), self.expression(), 
                    self.symbol()]
        elif t in '-~': 
            return node + [self.unary_op()] + self.term() 
        else: 
            node += [self.identifier()] 
            t = self.lookahead
            if t == '[': 
                node += [self.symbol('['), 
                        self.expression(), self.symbol(']')] 
            elif t in '.(': 
                node += self.subroutine_call() 

            return node

    def expr_list(self): 
        if self.lookahead == ')': 
            return ['expressionList', []] 

        node = ['expressionList', self.expression()] 
        while self.lookahead == ',': 
            node += [self.symbol(), self.expression()] 

        return node 

    def int_const(self): 
        t = self.lookahead; 
        self.match(t) 
        return ['integerConstant', t] 

    def str_const(self): 
        t = self.lookahead; 
        self.match(t) 
        return ['stringConstant', t] 

    def op(self): 
        return self.symbol() 

    def unary_op(self): 
        return self.symbol() 

