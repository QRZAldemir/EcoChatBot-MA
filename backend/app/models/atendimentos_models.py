# app/models/atendimento.py
class Atendimentos(Base):
    __tablename__ = "atendimentos"
    
    id = Column(Integer, primary_key=True)
    protocolo = Column(String, unique=True)
    telefone = Column(String)
    nome_contato = Column(String)
    tipo_canal = Column(Integer)  # 1=WhatsApp, 2=Interno
    canal_id = Column(Integer, ForeignKey("canais.id"))
    tipo = Column(Integer)  # 1=automático, 2=manual
    status = Column(String)  # aberto, fila, em_atendimento, finalizado
    departamento_id = Column(Integer, ForeignKey("departamentos.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    conexao_id = Column(Integer, ForeignKey("conexoes.id"))
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
