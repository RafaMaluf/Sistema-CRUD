import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox, QComboBox, QInputDialog
)
from sqlalchemy.orm import sessionmaker
from app import (
    engine, autenticar_usuario, create_cliente, read_cliente, update_cliente, delete_cliente,
    create_apolice, read_apolice, update_apolice, delete_apolice,
    create_apartamento, read_apartamento, update_apartamento, delete_apartamento,
    create_acidente, read_acidente, update_acidente, delete_acidente,
    get_apolices_com_clientes, contar_apartamentos_por_cidade, apolices_acima_de_valor
)

# Configuração da sessão
Session = sessionmaker(bind=engine)
session = Session()

import json
from sqlalchemy.sql import text
from datetime import date, datetime


def save_checkpoint(session, savepoint_name):
    try:
        # Função auxiliar para transformar resultados em dicionários
        def rows_to_dicts(cursor, rows):
            columns = [col[0] for col in cursor.description]  # Extrai os nomes das colunas
            data = []
            for row in rows:
                row_dict = {}
                for col_name, value in zip(columns, row):
                    # Converte data/datetime para string
                    if isinstance(value, (date, datetime)):
                        row_dict[col_name] = value.strftime("%Y-%m-%d")
                    else:
                        row_dict[col_name] = value
                data.append(row_dict)
            return data

        # Extrair dados das tabelas
        with engine.connect() as connection:
            clientes = connection.execute(text("SELECT * FROM clientes"))
            clientes_data = rows_to_dicts(clientes.cursor, clientes.fetchall())

            apolices = connection.execute(text("SELECT * FROM apolices"))
            apolices_data = rows_to_dicts(apolices.cursor, apolices.fetchall())

            apartamentos = connection.execute(text("SELECT * FROM apartamentos"))
            apartamentos_data = rows_to_dicts(apartamentos.cursor, apartamentos.fetchall())

            acidentes = connection.execute(text("SELECT * FROM acidentes"))
            acidentes_data = rows_to_dicts(acidentes.cursor, acidentes.fetchall())

        # Converter os dados para JSON
        checkpoint_data = {
            "clientes": clientes_data,
            "apolices": apolices_data,
            "apartamentos": apartamentos_data,
            "acidentes": acidentes_data
        }

        # Inserir o checkpoint no banco
        session.execute(
            text("INSERT INTO checkpoints (savepoint_name, data_backup) VALUES (:name, :data)"),
            {"name": savepoint_name, "data": json.dumps(checkpoint_data)}
        )
        session.commit()
        QMessageBox.information(None, "Checkpoint", f"Checkpoint '{savepoint_name}' salvo com sucesso!")
    except Exception as e:
        QMessageBox.warning(None, "Erro", f"Erro ao salvar checkpoint: {e}")

def rollback_to_checkpoint(session, savepoint_name):
    try:
        # Recuperar o checkpoint
        result = session.execute(
            text("SELECT data_backup FROM checkpoints WHERE savepoint_name = :name"),
            {"name": savepoint_name}
        ).fetchone()

        if not result:
            QMessageBox.warning(None, "Erro", f"Checkpoint '{savepoint_name}' não encontrado.")
            return

        # O dado JSON está no índice 0 da tupla retornada
        checkpoint_data = json.loads(result[0])

        # Restaurar os dados seguindo a ordem correta de deleção
        session.execute(text("DELETE FROM acidentes"))
        session.execute(text("DELETE FROM apartamentos"))
        session.execute(text("DELETE FROM apolices"))
        session.execute(text("DELETE FROM clientes"))

        # Inserir os dados de volta
        for cliente in checkpoint_data["clientes"]:
            session.execute(
                text("INSERT INTO clientes (cpf, nome, contato, data_nascimento, sexo) VALUES (:cpf, :nome, :contato, :data_nascimento, :sexo)"),
                cliente
            )

        for apolice in checkpoint_data["apolices"]:
            session.execute(
                text("INSERT INTO apolices (n_seguro, data_inicio, valor_mensal, cobertura, fk_cpf) VALUES (:n_seguro, :data_inicio, :valor_mensal, :cobertura, :fk_cpf)"),
                apolice
            )

        for apartamento in checkpoint_data["apartamentos"]:
            session.execute(
                text("INSERT INTO apartamentos (logradouro, cidade, metragem, fk_seguro, valor_mercado, n_moradores) VALUES (:logradouro, :cidade, :metragem, :fk_seguro, :valor_mercado, :n_moradores)"),
                apartamento
            )

        for acidente in checkpoint_data["acidentes"]:
            session.execute(
                text("INSERT INTO acidentes (id_acidente, data, qtd_acidentes, fk_apartamento, descricao, envolvidos) VALUES (:id_acidente, :data, :qtd_acidentes, :fk_apartamento, :descricao, :envolvidos)"),
                acidente
            )

        session.commit()
        QMessageBox.information(None, "Rollback", f"Rollback realizado para '{savepoint_name}'.")
    except Exception as e:
        QMessageBox.warning(None, "Erro", f"Erro ao realizar rollback: {e}")


button_style = """
    QPushButton {
        background-color: #4a90e2;
        color: white;
        padding: 8px;
        border-radius: 5px;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #357ABD;
    }
"""

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Sistema de Gestão")
        self.setGeometry(100, 100, 300, 200)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuário")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)
        self.login_button.setStyleSheet(button_style)

        self.setLayout(layout)

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        # Autentica o usuário e recupera seu papel
        user = autenticar_usuario(session, username, password)
        if user:
            QMessageBox.information(self, "Sucesso", f"Bem-vindo, {user.username}!")
            self.main_window = MainMenu(user.username, user.role)  # Passa o `role` para o MainMenu
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, "Erro", "Usuário ou senha inválidos.")

class MainMenu(QWidget):
    def __init__(self, username, role):
        super().__init__()
        self.username = username
        self.role = role  # Recebe o papel do usuário
        self.setWindowTitle("Menu Principal")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel(f"Bem-vindo, {self.username} ({self.role.capitalize()})")
        layout.addWidget(self.label)

        # Funções disponíveis para administradores
        if self.role == "admin":
            self.crud_button = QPushButton("Funções CRUD")
            self.crud_button.clicked.connect(self.show_crud_menu)
            layout.addWidget(self.crud_button)
            self.crud_button.setStyleSheet(button_style)

            self.transaction_button = QPushButton("Gerenciamento de Transações")
            self.transaction_button.clicked.connect(self.show_transaction_menu)
            layout.addWidget(self.transaction_button)
            self.transaction_button.setStyleSheet(button_style)

        # Consultas avançadas disponíveis para todos
        self.query_button = QPushButton("Consultas Avançadas")
        self.query_button.clicked.connect(self.show_advanced_queries)
        layout.addWidget(self.query_button)
        self.query_button.setStyleSheet(button_style)

        self.setLayout(layout)

    def show_crud_menu(self):
        self.crud_menu = CRUDMenu(self)
        self.crud_menu.show()
        self.close()

    def show_advanced_queries(self):
        self.query_window = AdvancedQueryWindow(self)
        self.query_window.show()
        self.close()

    def show_transaction_menu(self):
        self.transaction_menu = TransactionMenu(self)
        self.transaction_menu.show()
        self.close()

class TransactionMenu(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Gerenciamento de Transações")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel("Gerenciamento de Transações")
        layout.addWidget(self.label)

        self.savepoint_input = QLineEdit()
        self.savepoint_input.setPlaceholderText("Nome do Savepoint")
        layout.addWidget(self.savepoint_input)

        self.create_savepoint_button = QPushButton("Criar Savepoint")
        self.create_savepoint_button.clicked.connect(self.create_savepoint)
        layout.addWidget(self.create_savepoint_button)
        self.create_savepoint_button.setStyleSheet(button_style)

        self.rollback_button = QPushButton("Rollback para Savepoint")
        self.rollback_button.clicked.connect(self.rollback_savepoint)
        layout.addWidget(self.rollback_button)
        self.rollback_button.setStyleSheet(button_style)


        self.back_button = QPushButton("Voltar")
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)
        self.back_button.setStyleSheet(button_style)

        self.setLayout(layout)

    def create_savepoint(self):
        savepoint_name = self.savepoint_input.text()
        if savepoint_name:
            save_checkpoint(session, savepoint_name)

    def rollback_savepoint(self):
        savepoint_name = self.savepoint_input.text()
        if savepoint_name:
            rollback_to_checkpoint(session, savepoint_name)


    def go_back(self):
        self.parent.show()
        self.close()


class CRUDMenu(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("CRUD - Seleção de Entidade")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel("Selecione uma entidade para realizar operações CRUD:")
        layout.addWidget(self.label)

        self.entityComboBox = QComboBox()
        self.entityComboBox.addItems(["Cliente", "Apólice", "Apartamento", "Acidente"])
        layout.addWidget(self.entityComboBox)

        self.select_button = QPushButton("Avançar")
        self.select_button.clicked.connect(self.proceed_to_crud)
        layout.addWidget(self.select_button)
        self.select_button.setStyleSheet(button_style)

        self.back_button = QPushButton("Voltar")
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)
        self.back_button.setStyleSheet(button_style)

        self.setLayout(layout)

    def proceed_to_crud(self):
        selected_entity = self.entityComboBox.currentText()
        self.crud_operations = CRUDOperations(selected_entity, self)
        self.crud_operations.show()
        self.close()

    def go_back(self):
        self.parent.show()
        self.close()


class CRUDOperations(QWidget):
    def __init__(self, entity, parent):
        super().__init__()
        self.entity = entity
        self.parent = parent
        self.setWindowTitle(f"CRUD - {entity}")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel(f"Selecione uma operação para {self.entity}:")
        layout.addWidget(self.label)

        self.create_button = QPushButton("Criar")
        self.create_button.clicked.connect(lambda: self.open_crud_window('create'))
        layout.addWidget(self.create_button)
        self.create_button.setStyleSheet(button_style)

        self.read_button = QPushButton("Ler")
        self.read_button.clicked.connect(lambda: self.open_crud_window('read'))
        layout.addWidget(self.read_button)
        self.read_button.setStyleSheet(button_style)

        self.update_button = QPushButton("Atualizar")
        self.update_button.clicked.connect(lambda: self.open_crud_window('update'))
        layout.addWidget(self.update_button)
        self.update_button.setStyleSheet(button_style)

        self.delete_button = QPushButton("Deletar")
        self.delete_button.clicked.connect(lambda: self.open_crud_window('delete'))
        layout.addWidget(self.delete_button)
        self.delete_button.setStyleSheet(button_style)

        self.back_button = QPushButton("Voltar")
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)
        self.back_button.setStyleSheet(button_style)

        self.setLayout(layout)

    def open_crud_window(self, operation):
        self.crud_window = CRUDWindow(self.entity, operation, self)
        self.crud_window.show()
        self.close()

    def go_back(self):
        self.parent.show()
        self.close()


class CRUDWindow(QWidget):
    def __init__(self, entity, operation, parent):
        super().__init__()
        self.entity = entity
        self.operation = operation
        self.parent = parent
        self.setWindowTitle(f"{operation.capitalize()} - {entity}")
        self.setGeometry(100, 100, 400, 400)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel(f"{self.operation.capitalize()} {self.entity}")
        layout.addWidget(self.label)

        # Campos para CRUD de Cliente
        if self.entity == "Cliente":
            self.cpf_input = QLineEdit()
            self.cpf_input.setPlaceholderText("CPF")
            layout.addWidget(self.cpf_input)

            if (self.operation != "delete" and self.operation != "read"):
                self.nome_input = QLineEdit()
                self.nome_input.setPlaceholderText("Nome")
                layout.addWidget(self.nome_input)

                self.contato_input = QLineEdit()
                self.contato_input.setPlaceholderText("Contato")
                layout.addWidget(self.contato_input)

                self.data_nascimento_input = QLineEdit()
                self.data_nascimento_input.setPlaceholderText("Data de Nascimento (YYYY-MM-DD)")
                layout.addWidget(self.data_nascimento_input)

                self.sexo_input = QLineEdit()
                self.sexo_input.setPlaceholderText("Sexo")
                layout.addWidget(self.sexo_input)

        # Campos para CRUD de Apólice
        elif self.entity == "Apólice":
            self.n_seguro_input = QLineEdit()
            self.n_seguro_input.setPlaceholderText("Número do Seguro")
            layout.addWidget(self.n_seguro_input)

            if (self.operation != "delete" and self.operation != "read"):
                self.data_inicio_input = QLineEdit()
                self.data_inicio_input.setPlaceholderText("Data de Início (YYYY-MM-DD)")
                layout.addWidget(self.data_inicio_input)

                self.valor_mensal_input = QLineEdit()
                self.valor_mensal_input.setPlaceholderText("Valor Mensal")
                layout.addWidget(self.valor_mensal_input)

                self.cobertura_input = QLineEdit()
                self.cobertura_input.setPlaceholderText("Cobertura")
                layout.addWidget(self.cobertura_input)

                self.fk_cpf_input = QLineEdit()
                self.fk_cpf_input.setPlaceholderText("CPF do Cliente")
                layout.addWidget(self.fk_cpf_input)

        # Campos para CRUD de Apartamento
        elif self.entity == "Apartamento":
            self.logradouro_input = QLineEdit()
            self.logradouro_input.setPlaceholderText("Logradouro")
            layout.addWidget(self.logradouro_input)

            if (self.operation != "delete" and self.operation != "read"):
                self.cidade_input = QLineEdit()
                self.cidade_input.setPlaceholderText("Cidade")
                layout.addWidget(self.cidade_input)

                self.metragem_input = QLineEdit()
                self.metragem_input.setPlaceholderText("Metragem")
                layout.addWidget(self.metragem_input)

                self.fk_seguro_input = QLineEdit()
                self.fk_seguro_input.setPlaceholderText("Número do Seguro")
                layout.addWidget(self.fk_seguro_input)

                self.valor_mercado_input = QLineEdit()
                self.valor_mercado_input.setPlaceholderText("Valor de Mercado")
                layout.addWidget(self.valor_mercado_input)

                self.n_moradores_input = QLineEdit()
                self.n_moradores_input.setPlaceholderText("Número de Moradores")
                layout.addWidget(self.n_moradores_input)

        # Campos para CRUD de Acidente
        elif self.entity == "Acidente":
            self.id_acidente_input = QLineEdit()
            self.id_acidente_input.setPlaceholderText("ID do Acidente")
            layout.addWidget(self.id_acidente_input)

            if (self.operation != "delete" and self.operation != "read"):
                self.data_input = QLineEdit()
                self.data_input.setPlaceholderText("Data do Acidente (YYYY-MM-DD)")
                layout.addWidget(self.data_input)

                self.qtd_acidentes_input = QLineEdit()
                self.qtd_acidentes_input.setPlaceholderText("Quantidade de Acidentes")
                layout.addWidget(self.qtd_acidentes_input)

                self.fk_apartamento_input = QLineEdit()
                self.fk_apartamento_input.setPlaceholderText("Logradouro do Apartamento")
                layout.addWidget(self.fk_apartamento_input)

                self.descricao_input = QLineEdit()
                self.descricao_input.setPlaceholderText("Descrição")
                layout.addWidget(self.descricao_input)

                self.envolvidos_input = QLineEdit()
                self.envolvidos_input.setPlaceholderText("Número de Envolvidos")
                layout.addWidget(self.envolvidos_input)

        # Botões
        self.execute_button = QPushButton("Executar")
        self.execute_button.clicked.connect(self.execute_operation)
        layout.addWidget(self.execute_button)
        self.execute_button.setStyleSheet(button_style)

        self.back_button = QPushButton("Voltar")
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)
        self.back_button.setStyleSheet(button_style)

        self.setLayout(layout)

    def execute_operation(self):
        if self.entity == "Cliente":
            cpf = self.cpf_input.text()

            if self.operation == "create":
                nome = self.nome_input.text()
                contato = self.contato_input.text()
                data_nascimento = self.data_nascimento_input.text()
                sexo = self.sexo_input.text()
                create_cliente(session, cpf, nome, contato, data_nascimento, sexo)
                QMessageBox.information(self, "Sucesso", "Cliente criado com sucesso!")

            elif self.operation == "read":
                cliente = read_cliente(session, cpf)
                if cliente:
                    QMessageBox.information(self, "Cliente encontrado",
                                            f"Nome: {cliente.nome}\nContato: {cliente.contato}\nData Nasc.: {cliente.data_nascimento}\nSexo: {cliente.sexo}")
                else:
                    QMessageBox.warning(self, "Erro", "Cliente não encontrado.")

            elif self.operation == "update":
                nome = self.nome_input.text() or None
                contato = self.contato_input.text() or None
                data_nascimento = self.data_nascimento_input.text() or None
                sexo = self.sexo_input.text() or None
                update_cliente(session, cpf, nome, contato, data_nascimento, sexo)
                QMessageBox.information(self, "Sucesso", "Cliente atualizado com sucesso!")

            elif self.operation == "delete":
                delete_cliente(session, cpf)
                QMessageBox.information(self, "Sucesso", "Cliente deletado com sucesso!")

        elif self.entity == "Apólice":
            n_seguro = self.n_seguro_input.text()

            if self.operation == "create":
                data_inicio = self.data_inicio_input.text()
                valor_mensal = int(self.valor_mensal_input.text())
                cobertura = self.cobertura_input.text()
                fk_cpf = self.fk_cpf_input.text()
                create_apolice(session, n_seguro, data_inicio, valor_mensal, cobertura, fk_cpf)
                QMessageBox.information(self, "Sucesso", "Apólice criada com sucesso!")

            elif self.operation == "read":
                apolice = read_apolice(session, n_seguro)
                if apolice:
                    QMessageBox.information(self, "Apólice encontrada",
                                            f"Data Início: {apolice.data_inicio}\nValor Mensal: {apolice.valor_mensal}\nCobertura: {apolice.cobertura}")
                else:
                    QMessageBox.warning(self, "Erro", "Apólice não encontrada.")

            elif self.operation == "update":
                data_inicio = self.data_inicio_input.text() or None
                valor_mensal = int(self.valor_mensal_input.text()) if self.valor_mensal_input.text() else None
                cobertura = self.cobertura_input.text() or None
                fk_cpf = self.fk_cpf_input.text() or None
                update_apolice(session, n_seguro, data_inicio, valor_mensal, cobertura, fk_cpf)
                QMessageBox.information(self, "Sucesso", "Apólice atualizada com sucesso!")

            elif self.operation == "delete":
                delete_apolice(session, n_seguro)
                QMessageBox.information(self, "Sucesso", "Apólice deletada com sucesso!")

        elif self.entity == "Apartamento":
            logradouro = self.logradouro_input.text()

            if self.operation == "create":
                cidade = self.cidade_input.text()
                metragem = int(self.metragem_input.text())
                fk_seguro = self.fk_seguro_input.text()
                valor_mercado = int(self.valor_mercado_input.text())
                n_moradores = int(self.n_moradores_input.text())
                create_apartamento(session, logradouro, cidade, metragem, fk_seguro, valor_mercado, n_moradores)
                QMessageBox.information(self, "Sucesso", "Apartamento criado com sucesso!")

            elif self.operation == "read":
                apartamento = read_apartamento(session, logradouro)
                if apartamento:
                    QMessageBox.information(self, "Apartamento encontrado",
                                            f"Cidade: {apartamento.cidade}\nMetragem: {apartamento.metragem}\nValor de Mercado: {apartamento.valor_mercado}\nNúmero de Moradores: {apartamento.n_moradores}")
                else:
                    QMessageBox.warning(self, "Erro", "Apartamento não encontrado.")

            elif self.operation == "update":
                cidade = self.cidade_input.text() or None
                metragem = int(self.metragem_input.text()) if self.metragem_input.text() else None
                fk_seguro = self.fk_seguro_input.text() or None
                valor_mercado = int(self.valor_mercado_input.text()) if self.valor_mercado_input.text() else None
                n_moradores = int(self.n_moradores_input.text()) if self.n_moradores_input.text() else None
                update_apartamento(session, logradouro, cidade, metragem, fk_seguro, valor_mercado, n_moradores)
                QMessageBox.information(self, "Sucesso", "Apartamento atualizado com sucesso!")

            elif self.operation == "delete":
                delete_apartamento(session, logradouro)
                QMessageBox.information(self, "Sucesso", "Apartamento deletado com sucesso!")

        elif self.entity == "Acidente":
            id_acidente = self.id_acidente_input.text()

            if self.operation == "create":
                data = self.data_input.text()
                qtd_acidentes = int(self.qtd_acidentes_input.text())
                fk_apartamento = self.fk_apartamento_input.text()
                descricao = self.descricao_input.text()
                envolvidos = int(self.envolvidos_input.text())
                create_acidente(session, id_acidente, data, qtd_acidentes, fk_apartamento, descricao, envolvidos)
                QMessageBox.information(self, "Sucesso", "Acidente criado com sucesso!")

            elif self.operation == "read":
                acidente = read_acidente(session, id_acidente)
                if acidente:
                    QMessageBox.information(self, "Acidente encontrado",
                                            f"Data: {acidente.data}\nQtd Acidentes: {acidente.qtd_acidentes}\nDescrição: {acidente.descricao}\nEnvolvidos: {acidente.envolvidos}")
                else:
                    QMessageBox.warning(self, "Erro", "Acidente não encontrado.")

            elif self.operation == "update":
                data = self.data_input.text() or None
                qtd_acidentes = int(self.qtd_acidentes_input.text()) if self.qtd_acidentes_input.text() else None
                fk_apartamento = self.fk_apartamento_input.text() or None
                descricao = self.descricao_input.text() or None
                envolvidos = int(self.envolvidos_input.text()) if self.envolvidos_input.text() else None
                update_acidente(session, id_acidente, data, qtd_acidentes, fk_apartamento, descricao, envolvidos)
                QMessageBox.information(self, "Sucesso", "Acidente atualizado com sucesso!")

            elif self.operation == "delete":
                delete_acidente(session, id_acidente)
                QMessageBox.information(self, "Sucesso", "Acidente deletado com sucesso!")

    def go_back(self):
        self.parent.show()
        self.close()


class AdvancedQueryWindow(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Consultas Avançadas")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel("Selecione uma consulta avançada:")
        layout.addWidget(self.label)

        # Botão para listar apólices e clientes associados
        self.query1_button = QPushButton("Listar Apólices e Clientes Associados")
        self.query1_button.clicked.connect(self.query1)
        layout.addWidget(self.query1_button)
        self.query1_button.setStyleSheet(button_style)

        # Botão para contar apartamentos por cidade
        self.query2_button = QPushButton("Número de Apartamentos por Cidade")
        self.query2_button.clicked.connect(self.query2)
        layout.addWidget(self.query2_button)
        self.query2_button.setStyleSheet(button_style)

        # Botão para filtrar apólices acima de um valor específico
        self.query3_button = QPushButton("Apólices Acima de um Valor Específico")
        self.query3_button.clicked.connect(self.query3)
        layout.addWidget(self.query3_button)
        self.query3_button.setStyleSheet(button_style)

        # Botão para voltar ao menu principal
        self.back_button = QPushButton("Voltar")
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)
        self.back_button.setStyleSheet(button_style)

        self.setLayout(layout)

    def query1(self):
        """Consulta para listar apólices e seus clientes associados"""
        results = get_apolices_com_clientes(session)
        if results:
            output = "\n".join([f"Apólice: {a.n_seguro}, Cliente: {c.nome}" for a, c in results])
            QMessageBox.information(self, "Resultados", output)
        else:
            QMessageBox.warning(self, "Resultados", "Nenhuma apólice encontrada.")

    def query2(self):
        """Consulta para contar apartamentos por cidade"""
        results = contar_apartamentos_por_cidade(session)
        if results:
            output = "\n".join([f"Cidade: {cidade}, Total: {total}" for cidade, total in results])
            QMessageBox.information(self, "Resultados", output)
        else:
            QMessageBox.warning(self, "Resultados", "Nenhuma informação encontrada.")

    def query3(self):
        """Consulta para listar apólices acima de um valor específico"""
        valor_minimo, ok = QInputDialog.getInt(self, "Apólices por Valor", "Digite o valor mínimo:")
        if ok:
            results = apolices_acima_de_valor(session, valor_minimo)
            if results:
                output = "\n".join([f"Apólice: {a.n_seguro}, Valor: {a.valor_mensal}" for a in results])
                QMessageBox.information(self, "Resultados", output)
            else:
                QMessageBox.warning(self, "Resultados", "Nenhuma apólice encontrada acima do valor informado.")

    def go_back(self):
        """Voltar para o menu principal"""
        self.parent.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())