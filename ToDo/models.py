from dataclasses import dataclass, field
from datetime import datetime
from config import DATE_FORMAT, STATUS_PENDING, PRIORITY_MEDIUM

@dataclass
class Task:
    id:int=0
    titulo:str=""
    descripcion:str=""
    responsable:str=""
    estado:str=STATUS_PENDING
    prioridad:str=PRIORITY_MEDIUM
    categoria:str=""
    etiquetas:str=""
    fecha_creacion:str=""
    fecha_inicio:str=""
    fecha_prevista:str=""
    fecha_finalizacion:str=""
    avance:int=0
    comentarios:str=""
    historial:list=field(default_factory=list)

    def esta_retrasada(self)->bool:
        if self.estado=="Finalizada" or not self.fecha_prevista:
            return False
        try:
            limite=datetime.strptime(self.fecha_prevista, DATE_FORMAT).date()
            return datetime.today().date()>limite
        except Exception:
            return False

    def finalizar(self):
        self.estado="Finalizada"
        self.avance=100
        self.fecha_finalizacion=datetime.now().strftime(DATE_FORMAT)

    def agregar_historial(self, usuario:str, avance:int, comentario:str):
        self.historial.append({
            "fecha":datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "usuario":usuario,
            "avance":avance,
            "comentario":comentario
        })
