import pymysql
from sqlalchemy import create_engine, Column, String, Date, Integer, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Configuração do banco de dados
DB_USER = 'root'
DB_PASSWORD = 'Gabisa-02'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'tde3'

# Criação do banco de dados
connection = pymysql.connect(
    host=DB_HOST,
    port=int(DB_PORT),
    user=DB_USER,
    password=DB_PASSWORD,
)

try:
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    connection.commit()
finally:
    connection.close()

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Definição das tabelas
class Cliente(Base):
    __tablename__ = 'clientes'
    cpf = Column(String(11), primary_key=True)
    nome = Column(String(100))
    contato = Column(String(50))
    data_nascimento = Column(Date)
    sexo = Column(String(10))
    apolices = relationship("Apolice", back_populates="CLIENTE")

class Apolice(Base):
    __tablename__ = 'apolices'
    n_seguro = Column(String(20), primary_key=True)
    data_inicio = Column(Date)
    valor_mensal = Column(Integer)
    cobertura = Column(String(100))
    fk_cpf = Column(String(11), ForeignKey('clientes.cpf'))
    cliente = relationship("Cliente", back_populates="apolices")
    apartamentos = relationship("Apartamento", back_populates="apolice")

class Apartamento(Base):
    __tablename__ = 'apartamentos'
    logradouro = Column(String(100), primary_key=True)
    cidade = Column(String(50))
    metragem = Column(Integer)
    fk_seguro = Column(String(20), ForeignKey('apolices.n_seguro'))
    valor_mercado = Column(Integer)
    n_moradores = Column(Integer)
    apolice = relationship("Apolice", back_populates="apartamentos")
    acidentes = relationship("Acidente", back_populates="apartamento")

class Acidente(Base):
    __tablename__ = 'acidentes'
    id_acidente = Column(Integer, primary_key=True)
    data = Column(Date)
    qtd_acidentes = Column(Integer)
    fk_apartamento = Column(String(100), ForeignKey('apartamentos.logradouro'))
    descricao = Column(String(255))
    envolvidos = Column(Integer)
    apartamento = relationship("Apartamento", back_populates="acidentes")

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False)  # admin ou user

# Criação das tabelas
def create_tables():
    Base.metadata.create_all(engine)

# Funções CRUD - Cliente
def create_cliente(session, cpf, nome, contato, data_nascimento, sexo):
    cliente = Cliente(cpf=cpf, nome=nome, contato=contato, data_nascimento=data_nascimento, sexo=sexo)
    session.add(cliente)
    session.commit()

def read_cliente(session, cpf):
    return session.query(Cliente).filter_by(cpf=cpf).first()

def update_cliente(session, cpf, nome=None, contato=None, data_nascimento=None, sexo=None):
    cliente = session.query(Cliente).filter_by(cpf=cpf).first()
    if cliente:
        if nome: cliente.nome = nome
        if contato: cliente.contato = contato
        if data_nascimento: cliente.data_nascimento = data_nascimento
        if sexo: cliente.sexo = sexo
        session.commit()

def delete_cliente(session, cpf):
    cliente = session.query(Cliente).filter_by(cpf=cpf).first()
    if cliente:
        session.delete(cliente)
        session.commit()

# Funções CRUD - Apólice
def create_apolice(session, n_seguro, data_inicio, valor_mensal, cobertura, fk_cpf):
    apolice = Apolice(n_seguro=n_seguro, data_inicio=data_inicio, valor_mensal=valor_mensal, cobertura=cobertura, fk_cpf=fk_cpf)
    session.add(apolice)
    session.commit()

def read_apolice(session, n_seguro):
    return session.query(Apolice).filter_by(n_seguro=n_seguro).first()

def update_apolice(session, n_seguro, data_inicio=None, valor_mensal=None, cobertura=None, fk_cpf=None):
    apolice = session.query(Apolice).filter_by(n_seguro=n_seguro).first()
    if apolice:
        if data_inicio: apolice.data_inicio = data_inicio
        if valor_mensal: apolice.valor_mensal = valor_mensal
        if cobertura: apolice.cobertura = cobertura
        if fk_cpf: apolice.fk_cpf = fk_cpf
        session.commit()

def delete_apolice(session, n_seguro):
    apolice = session.query(Apolice).filter_by(n_seguro=n_seguro).first()
    if apolice:
        session.delete(apolice)
        session.commit()

# Funções CRUD - Apartamento
def create_apartamento(session, logradouro, cidade, metragem, fk_seguro, valor_mercado, n_moradores):
    apartamento = Apartamento(logradouro=logradouro, cidade=cidade, metragem=metragem, fk_seguro=fk_seguro, valor_mercado=valor_mercado, n_moradores=n_moradores)
    session.add(apartamento)
    session.commit()

def read_apartamento(session, logradouro):
    return session.query(Apartamento).filter_by(logradouro=logradouro).first()

def update_apartamento(session, logradouro, cidade=None, metragem=None, fk_seguro=None, valor_mercado=None, n_moradores=None):
    apartamento = session.query(Apartamento).filter_by(logradouro=logradouro).first()
    if apartamento:
        if cidade: apartamento.cidade = cidade
        if metragem: apartamento.metragem = metragem
        if fk_seguro: apartamento.fk_seguro = fk_seguro
        if valor_mercado: apartamento.valor_mercado = valor_mercado
        if n_moradores: apartamento.n_moradores = n_moradores
        session.commit()

def delete_apartamento(session, logradouro):
    apartamento = session.query(Apartamento).filter_by(logradouro=logradouro).first()
    if apartamento:
        session.delete(apartamento)
        session.commit()

# Funções CRUD - Acidente
def create_acidente(session, id_acidente, data, qtd_acidentes, fk_apartamento, descricao, envolvidos):
    acidente = Acidente(id_acidente=id_acidente, data=data, qtd_acidentes=qtd_acidentes, fk_apartamento=fk_apartamento, descricao=descricao, envolvidos=envolvidos)
    session.add(acidente)
    session.commit()

def read_acidente(session, id_acidente):
    return session.query(Acidente).filter_by(id_acidente=id_acidente).first()

def update_acidente(session, id_acidente, data=None, qtd_acidentes=None, fk_apartamento=None, descricao=None, envolvidos=None):
    acidente = session.query(Acidente).filter_by(id_acidente=id_acidente).first()
    if acidente:
        if data: acidente.data = data
        if qtd_acidentes: acidente.qtd_acidentes = qtd_acidentes
        if fk_apartamento: acidente.fk_apartamento = fk_apartamento
        if descricao: acidente.descricao = descricao
        if envolvidos: acidente.envolvidos = envolvidos
        session.commit()

def delete_acidente(session, id_acidente):
    acidente = session.query(Acidente).filter_by(id_acidente=id_acidente).first()
    if acidente:
        session.delete(acidente)
        session.commit()

# Controle de acesso
def autenticar_usuario(session, username, password):
    return session.query(Usuario).filter_by(username=username, password=password).first()

def criar_usuario(session, username, password, role):
    usuario = Usuario(username=username, password=password, role=role)
    session.add(usuario)
    session.commit()

# Consultas avançadas
def get_apolices_com_clientes(session):
    return session.query(Apolice, Cliente).join(Cliente, Apolice.fk_cpf == Cliente.cpf).all()

def contar_apartamentos_por_cidade(session):
    return session.query(Apartamento.cidade, func.count(Apartamento.logradouro).label('total_apartamentos')).group_by(Apartamento.cidade).all()

def apolices_acima_de_valor(session, valor_minimo):
    return session.query(Apolice).filter(Apolice.valor_mensal > valor_minimo).all()

# Main
if __name__ == "__main__":
    create_tables()
    print("Tabelas criadas com sucesso!")
