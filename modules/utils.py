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


def calcula_seculo(data: str):
    # check if date contains a.C
    if data.find("a.C") != -1:
        ano = int(data.split()[0])

        # Calcula o século
        seculo = ((ano - 1) // 100) + 1

        # Formata a string de retorno
        seculo_formatado = "{} a.C.".format(seculo)

        return seculo_formatado
    else:
        ano = int(data.split()[-1])
        if ano % 100 == 0:
            ano -= 1
        seculo_formatado = (ano // 100) + 1

        return seculo_formatado