# app/models/atendimento_context.py
class AtendimentoContext(Base):
    __tablename__ = "atendimento_context"
    
    id = Column(Integer, primary_key=True)
    atendimento_id = Column(Integer, ForeignKey("atendimentos.id"))
    context_key = Column(String)
    value = Column(String)  # Armazenado como JSON string
    criado_em = Column(DateTime, default=datetime.utcnow)
