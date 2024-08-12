import os
import chardet


def detect_encoding(file_path):
    """Detecta la codificación de un archivo."""
    with open(file_path, 'rb') as file:
        result = chardet.detect(file.read())
    return result['encoding']


def convert_to_utf8(file_path):
    """Convierte un archivo a UTF-8 si no está ya en UTF-8."""
    encoding = detect_encoding(file_path)
    if encoding.lower() != 'utf-8':
        print(f'Convirtiendo {file_path} de {encoding} a UTF-8...')
        with open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f'Archivo {file_path} convertido a UTF-8.')
    else:
        print(f'Archivo {file_path} ya está en UTF-8.')


def find_requirements_files(root_dir):
    """Encuentra todos los archivos requirements.txt en un directorio."""
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file == 'requirements.txt':
                yield os.path.join(subdir, file)


def main():
    root_dir = 'modules'
    print('Buscando archivos requirements.txt...')
    for req_file in find_requirements_files(root_dir):
        convert_to_utf8(req_file)
    print('Proceso completado.')


if __name__ == '__main__':
    main()
