import os
import csv
import requests
import pyfiglet
from cryptography.fernet import Fernet

class GitHubOSINT:
    def __init__(self):
        self.config_file = "github_osint_config.enc"
        self.key_file = "github_osint_key.key"
        self.api_key = None
        self.show_banner()
        self.load_or_request_api_key()

    def show_banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        banner = pyfiglet.figlet_format("GITHUB OSINT", font="slant")
        print(banner)
        print("🔎 Herramienta OSINT para buscar usuarios y repositorios en GitHub")
        print("⌨️ Creado por @ivancastl")
        print("=" * 60)

    def get_encryption_key(self):
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
        else:
            with open(self.key_file, "rb") as f:
                key = f.read()
        return key

    def encrypt_api_key(self, api_key):
        key = self.get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(api_key.encode())
        with open(self.config_file, "wb") as f:
            f.write(encrypted)

    def decrypt_api_key(self):
        key = self.get_encryption_key()
        fernet = Fernet(key)
        with open(self.config_file, "rb") as f:
            encrypted = f.read()
        return fernet.decrypt(encrypted).decode()

    def load_or_request_api_key(self):
        if os.path.exists(self.config_file):
            try:
                self.api_key = self.decrypt_api_key()
            except Exception as e:
                print("❌ Error al leer la clave API encriptada:", e)
                self.request_and_save_api_key()
        else:
            self.request_and_save_api_key()

    def request_and_save_api_key(self):
        api_key = input("🔐 Introduce tu GitHub API Token (github_pat_...): ").strip()
        self.encrypt_api_key(api_key)
        self.api_key = api_key
        print("✅ API key guardada encriptada con éxito.\n")

# ---------- MODO 1: Buscar Usuarios ----------
def buscar_usuarios_github(token, keywords, max_results=100):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    keywords = [kw.strip() for kw in keywords.split(',')]
    resultados = []

    for keyword in keywords:
        print(f"\n🔍 Buscando usuarios con la palabra clave: {keyword}")
        page = 1

        while len(resultados) < max_results:
            params = {
                'q': keyword,
                'per_page': 100,
                'page': page
            }
            response = requests.get("https://api.github.com/search/users", headers=headers, params=params)
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code} - {response.text}")
                break

            data = response.json()
            users = data.get('items', [])
            if not users:
                break

            for user in users:
                username = user['login']
                detail_url = f"https://api.github.com/users/{username}"
                detail_response = requests.get(detail_url, headers=headers)
                if detail_response.status_code == 200:
                    detail = detail_response.json()
                    resultados.append({
                        'login': detail.get('login', ''),
                        'name': detail.get('name', ''),
                        'url': detail.get('html_url', ''),
                        'bio': detail.get('bio', ''),
                        'location': detail.get('location', ''),
                        'email': detail.get('email', ''),
                        'followers': detail.get('followers', ''),
                        'public_repos': detail.get('public_repos', ''),
                        'created_at': detail.get('created_at', ''),
                        'score': user.get('score', '')
                    })
                    if len(resultados) >= max_results:
                        break
            page += 1
    return resultados[:max_results]

def guardar_usuarios_csv(datos, nombre_archivo):
    with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo:
        writer = csv.writer(archivo)
        writer.writerow(['Usuario', 'Nombre', 'Perfil', 'Bio', 'Ubicación', 'Email', 'Seguidores', 'Repos Públicos', 'Creado en', 'Relevancia'])
        for u in datos:
            writer.writerow([
                u['login'], u['name'], u['url'], u['bio'], u['location'], u['email'],
                u['followers'], u['public_repos'], u['created_at'], u['score']
            ])

# ---------- MODO 2: Buscar Repositorios ----------
def buscar_repositorios_github(token, keywords, max_results=100):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    keywords = [kw.strip().lower() for kw in keywords.split(',')]
    resultados = []

    for keyword in keywords:
        print(f"\n📦 Buscando repositorios para: {keyword}")
        page = 1

        while len(resultados) < max_results:
            params = {
                'q': keyword,
                'sort': 'stars',
                'order': 'desc',
                'per_page': 100,
                'page': page
            }
            response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params)
            if response.status_code != 200:
                print(f"❌ Error en la consulta: {response.status_code} - {response.text}")
                break

            data = response.json()
            items = data.get('items', [])
            if not items:
                break

            for repo in items:
                name = repo['name'].lower()
                description = (repo['description'] or '').lower()
                if any(kw in name or kw in description for kw in keywords):
                    resultados.append(repo)
                    if len(resultados) >= max_results:
                        break
            page += 1

    vistos = set()
    unicos = []
    for r in resultados:
        if r['id'] not in vistos:
            unicos.append(r)
            vistos.add(r['id'])

    return unicos[:max_results]

def guardar_repos_csv(resultados, filename="repositorios_osint.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Nombre', 'URL', 'Descripción', 'Estrellas'])
        for repo in resultados:
            writer.writerow([
                repo['full_name'],
                repo['html_url'],
                repo['description'] or '',
                repo['stargazers_count']
            ])

# ---------- MAIN ----------
def main():
    app = GitHubOSINT()
    print("\n¿🔎 Qué deseas hacer?")
    print("1. Buscar usuarios de GitHub por palabra clave")
    print("2. Buscar repositorios OSINT por palabra clave")
    opcion = input("Selecciona (1 o 2): ").strip()

    if opcion == "1":
        palabras = input("Palabras clave para buscar usuarios (separadas por coma): ").strip()
        max_res = int(input("¿Cuántos usuarios deseas obtener? (máx 1000): "))
        max_res = min(max_res, 1000)
        nombre_csv = input("Nombre para el archivo CSV de salida: ").strip()
        if not nombre_csv.endswith('.csv'):
            nombre_csv += '.csv'
        resultados = buscar_usuarios_github(app.api_key, palabras, max_res)
        guardar_usuarios_csv(resultados, nombre_csv)
        print(f"\n✅ {len(resultados)} usuarios guardados en: {nombre_csv}")

    elif opcion == "2":
        palabras = input("Palabras clave para buscar repositorios (separadas por coma): ").strip()
        max_res = int(input("¿Cuántos repositorios deseas obtener? (máx 1000): "))
        max_res = min(max_res, 1000)
        nombre_csv = input("Nombre para el archivo CSV de salida: ").strip()
        if not nombre_csv.endswith('.csv'):
            nombre_csv += '.csv'
        resultados = buscar_repositorios_github(app.api_key, palabras, max_res)
        guardar_repos_csv(resultados, nombre_csv)
        print(f"\n✅ {len(resultados)} repositorios guardados en: {nombre_csv}")
    
    else:
        print("❌ Opción inválida.")

if __name__ == "__main__":
    main()

