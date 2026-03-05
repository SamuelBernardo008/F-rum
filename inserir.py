from models.usuario import criar_usuario

#Alunos
criar_usuario("Alice Crunfli 3°B", "alice@gmail.com", "123456", "aluno")
criar_usuario("Daniela Calado 3°D", "daniela@gmail.com", "123456", "aluno")
criar_usuario("Pedro Gabriel 3°A", "pg@gmail.com", "123456", "aluno")
criar_usuario("Isadora Salgado 3°C", "isadora@gmail.com", "123456", "aluno")

#professores
criar_usuario("Carlos", "carlos@gmail.com", "123456", "professor")
criar_usuario("Maira", "maira@gmail.com", "123456", "professor")
criar_usuario("Angela", "angela@gmail.com", "123456", "professor")

#admins
criar_usuario("Thauany", "thauany@gmail.com", "123456", "admin")
criar_usuario("Samuel Benardo", "samuel@gmail.com", "123456", "admin")
criar_usuario("Mathias Antunes", "mathias@gmail.com", "123456", "admin")

print("Usuário criado com sucesso!")