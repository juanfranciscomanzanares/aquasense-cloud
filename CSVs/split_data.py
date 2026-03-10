import csv
import random
import math

def split_csv(input_file, parts=3):
    print(f"Leyendo {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"ERROR: No encuentro el archivo '{input_file}'. Asegúrate de que está en la misma carpeta.")
        return

    # Separar cabecera y datos
    header = lines[0]
    data = lines[1:]
    
    # Mezclar aleatoriamente
    random.shuffle(data)
    
    # Calcular tamaño de cada parte
    total_rows = len(data)
    chunk_size = math.ceil(total_rows / parts)
    
    print(f"Total filas: {total_rows}. Dividiendo en {parts} partes de aprox {chunk_size} filas.")

    # Dividir y guardar
    for i in range(parts):
        start = i * chunk_size
        end = start + chunk_size
        chunk = data[start:end]
        
        filename = f'datos_parte_{i+1}.csv'
        
        with open(filename, 'w', encoding='utf-8') as f_out:
            f_out.write(header)
            f_out.writelines(chunk)
            
        print(f"Generado: {filename} con {len(chunk)} registros.")

if __name__ == '__main__':
    split_csv('Temperatura.csv')