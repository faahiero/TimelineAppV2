import os
import art
import csv


# Limpar o console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


# Menu do programa
def menu():
    banner = art.text2art("Wikipedia GeoHist", font="small")
    print(banner)
    print("[1] - Buscar (Ex.: 'Machado de Assis')")
    print("[2] - Gerar visualização")
    print("[3] - Gerar visualização histórico de navegação")
    print("[0] - Encerrar")
    print()


def int_to_roman(input):
    if not isinstance(input, type(1)):
        raise Exception("expected integer")
    if not 0 < input < 4000:
        raise Exception("Argument must be between 1 and 3999")
    ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
    nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
    result = []
    for i in range(len(ints)):
        count = int(input / ints[i])
        result.append(nums[i] * count)
        input -= ints[i] * count
    return ''.join(result)


def write_to_csv(person_info, file_name):
    if not os.path.isfile(file_name):
        with open(file_name, 'a', newline='') as csvfile:
            fieldnames = person_info.keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(person_info)
    else:
        with open(file_name, 'r+', newline='') as csvfile:
            fieldnames = person_info.keys()
            reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            for row in reader:
                if row['Nome Completo'] == person_info['Nome Completo']:
                    return
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(person_info)

