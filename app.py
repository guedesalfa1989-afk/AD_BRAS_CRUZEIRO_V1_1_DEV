from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ad-bras-dev-v1-1'
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'data', 'database_dev.db')

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON')
    return c

def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c=db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS congregacoes(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,cidade TEXT DEFAULT 'Cruzeiro',estado TEXT DEFAULT 'SP');
    CREATE TABLE IF NOT EXISTS visitantes(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,telefone TEXT,whatsapp TEXT,endereco TEXT,bairro TEXT,cidade TEXT DEFAULT 'Cruzeiro',estado TEXT DEFAULT 'SP',cep TEXT,congregacao_id INTEGER,status TEXT DEFAULT 'Visitante',observacoes TEXT,criado_em TEXT,FOREIGN KEY(congregacao_id) REFERENCES congregacoes(id));
    CREATE TABLE IF NOT EXISTS visitas(id INTEGER PRIMARY KEY AUTOINCREMENT,visitante_id INTEGER NOT NULL,data_visita TEXT NOT NULL,culto_evento TEXT,responsavel TEXT,observacoes TEXT,FOREIGN KEY(visitante_id) REFERENCES visitantes(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS decisoes_espirituais(id INTEGER PRIMARY KEY AUTOINCREMENT,visitante_id INTEGER NOT NULL,tipo TEXT NOT NULL,data_decisao TEXT NOT NULL,local TEXT,responsavel TEXT,observacoes TEXT,FOREIGN KEY(visitante_id) REFERENCES visitantes(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS acompanhamentos(id INTEGER PRIMARY KEY AUTOINCREMENT,visitante_id INTEGER NOT NULL,data_acao TEXT NOT NULL,tipo TEXT NOT NULL,responsavel TEXT,resultado TEXT,proximo_contato TEXT,observacoes TEXT,FOREIGN KEY(visitante_id) REFERENCES visitantes(id) ON DELETE CASCADE);
    ''')
    if c.execute('SELECT COUNT(*) FROM congregacoes').fetchone()[0]==0:
        c.executemany('INSERT INTO congregacoes(nome,cidade,estado) VALUES(?,?,?)',[("Sede AD BRAS Cruzeiro","Cruzeiro","SP"),("Congregação Teste 01","Cruzeiro","SP"),("Congregação Teste 02","Lavrinhas","SP")])
    if c.execute('SELECT COUNT(*) FROM visitantes').fetchone()[0]==0:
        now=datetime.now().isoformat(timespec='seconds')
        c.executemany('''INSERT INTO visitantes(nome,telefone,whatsapp,endereco,bairro,cidade,estado,cep,congregacao_id,status,observacoes,criado_em) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',[
            ('João da Silva','(12) 99999-1111','(12) 99999-1111','Rua A, 100','Centro','Cruzeiro','SP','12700-000',1,'Em acompanhamento','Cadastro fictício DEV',now),
            ('Maria de Souza','(12) 99999-2222','(12) 99999-2222','Rua B, 20','Vila Nova','Cruzeiro','SP','12700-100',2,'Visitante','Cadastro fictício DEV',now),
            ('Pedro Santos','(12) 99999-3333','(12) 99999-3333','Rua C, 55','Centro','Lavrinhas','SP','12760-000',3,'Em discipulado','Cadastro fictício DEV',now)])
        c.executemany('INSERT INTO visitas(visitante_id,data_visita,culto_evento,responsavel,observacoes) VALUES(?,?,?,?,?)',[(1,'2026-08-01','Culto','Recepção','Primeira visita'),(1,'2026-08-15','Culto','Recepção','Retorno'),(2,'2026-08-10','Culto','Recepção','Primeira visita'),(3,'2026-07-20','Culto','Recepção','Primeira visita'),(3,'2026-08-03','Escola Bíblica','Recepção','Retorno'),(3,'2026-08-17','Culto','Recepção','Retorno')])
        c.execute("INSERT INTO decisoes_espirituais(visitante_id,tipo,data_decisao,local,responsavel,observacoes) VALUES(?,?,?,?,?,?)",(3,'Aceitou Jesus','2026-08-17','Congregação Teste 02','Pr. Teste','Registro fictício DEV'))
        c.execute("INSERT INTO acompanhamentos(visitante_id,data_acao,tipo,responsavel,resultado,proximo_contato,observacoes) VALUES(?,?,?,?,?,?,?)",(1,'2026-08-16','WhatsApp','Líder Teste','Contato realizado','2026-08-30','Registro fictício DEV'))
    c.commit(); c.close()

@app.route('/')
def index():
    c=db(); s={
      'visitantes':c.execute('SELECT COUNT(*) FROM visitantes').fetchone()[0],
      'visitas':c.execute('SELECT COUNT(*) FROM visitas').fetchone()[0],
      'decisoes':c.execute("SELECT COUNT(*) FROM decisoes_espirituais WHERE tipo='Aceitou Jesus'").fetchone()[0],
      'acomp':c.execute('SELECT COUNT(*) FROM acompanhamentos').fetchone()[0]}
    c.close(); return render_template('index.html',s=s)

@app.route('/visitantes')
def visitantes():
    keys=['q','cidade','bairro','congregacao_id','status','aceitou_jesus','primeira_de','primeira_ate','ultima_de','ultima_ate','min_visitas','max_visitas','acompanhamento_tipo','responsavel']
    f={k:request.args.get(k,'').strip() for k in keys}
    c=db(); sql='''SELECT v.*,c.nome congregacao,(SELECT MIN(data_visita) FROM visitas x WHERE x.visitante_id=v.id) primeira_visita,(SELECT MAX(data_visita) FROM visitas x WHERE x.visitante_id=v.id) ultima_visita,(SELECT COUNT(*) FROM visitas x WHERE x.visitante_id=v.id) total_visitas,EXISTS(SELECT 1 FROM decisoes_espirituais d WHERE d.visitante_id=v.id AND d.tipo='Aceitou Jesus') aceitou_jesus FROM visitantes v LEFT JOIN congregacoes c ON c.id=v.congregacao_id WHERE 1=1'''; p=[]
    if f['q']:
        sql+=' AND (v.nome LIKE ? OR v.telefone LIKE ? OR v.whatsapp LIKE ?)'; p += [f"%{f['q']}%"]*3
    if f['cidade']:
        sql+=' AND v.cidade=?'; p.append(f['cidade'])
    if f['bairro']:
        sql+=' AND v.bairro LIKE ?'; p.append(f"%{f['bairro']}%")
    if f['congregacao_id']:
        sql+=' AND v.congregacao_id=?'; p.append(f['congregacao_id'])
    if f['status']:
        sql+=' AND v.status=?'; p.append(f['status'])
    if f['aceitou_jesus']=='sim': sql+=" AND EXISTS(SELECT 1 FROM decisoes_espirituais d WHERE d.visitante_id=v.id AND d.tipo='Aceitou Jesus')"
    if f['aceitou_jesus']=='nao': sql+=" AND NOT EXISTS(SELECT 1 FROM decisoes_espirituais d WHERE d.visitante_id=v.id AND d.tipo='Aceitou Jesus')"
    if f['primeira_de']:
        sql+=' AND (SELECT MIN(data_visita) FROM visitas x WHERE x.visitante_id=v.id)>=?'; p.append(f['primeira_de'])
    if f['primeira_ate']:
        sql+=' AND (SELECT MIN(data_visita) FROM visitas x WHERE x.visitante_id=v.id)<=?'; p.append(f['primeira_ate'])
    if f['ultima_de']:
        sql+=' AND (SELECT MAX(data_visita) FROM visitas x WHERE x.visitante_id=v.id)>=?'; p.append(f['ultima_de'])
    if f['ultima_ate']:
        sql+=' AND (SELECT MAX(data_visita) FROM visitas x WHERE x.visitante_id=v.id)<=?'; p.append(f['ultima_ate'])
    if f['min_visitas']:
        sql+=' AND (SELECT COUNT(*) FROM visitas x WHERE x.visitante_id=v.id)>=?'; p.append(int(f['min_visitas']))
    if f['max_visitas']:
        sql+=' AND (SELECT COUNT(*) FROM visitas x WHERE x.visitante_id=v.id)<=?'; p.append(int(f['max_visitas']))
    if f['acompanhamento_tipo']:
        sql+=' AND EXISTS(SELECT 1 FROM acompanhamentos a WHERE a.visitante_id=v.id AND a.tipo=?)'; p.append(f['acompanhamento_tipo'])
    if f['responsavel']:
        sql+=' AND (EXISTS(SELECT 1 FROM visitas x WHERE x.visitante_id=v.id AND x.responsavel LIKE ?) OR EXISTS(SELECT 1 FROM acompanhamentos a WHERE a.visitante_id=v.id AND a.responsavel LIKE ?) OR EXISTS(SELECT 1 FROM decisoes_espirituais d WHERE d.visitante_id=v.id AND d.responsavel LIKE ?))'; z=f"%{f['responsavel']}%"; p += [z,z,z]
    sql+=' ORDER BY v.nome'; rows=c.execute(sql,p).fetchall(); congregacoes=c.execute('SELECT * FROM congregacoes ORDER BY nome').fetchall(); cidades=c.execute('SELECT DISTINCT cidade FROM visitantes ORDER BY cidade').fetchall(); c.close()
    return render_template('visitantes.html',visitantes=rows,f=f,congregacoes=congregacoes,cidades=cidades)

@app.route('/visitante/<int:id>')
def detalhe(id):
    c=db(); v=c.execute('SELECT * FROM visitantes WHERE id=?',(id,)).fetchone(); visitas=c.execute('SELECT * FROM visitas WHERE visitante_id=? ORDER BY data_visita DESC',(id,)).fetchall(); decisoes=c.execute('SELECT * FROM decisoes_espirituais WHERE visitante_id=? ORDER BY data_decisao DESC',(id,)).fetchall(); acomp=c.execute('SELECT * FROM acompanhamentos WHERE visitante_id=? ORDER BY data_acao DESC',(id,)).fetchall(); c.close(); return render_template('detalhe.html',v=v,visitas=visitas,decisoes=decisoes,acomp=acomp)

if __name__=='__main__':
    init_db(); app.run(host='0.0.0.0',port=5000)
