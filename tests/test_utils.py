import unittest
import os
import csv
import json
from unittest.mock import patch, mock_open, MagicMock

# Adiciona o diretório pai ao sys.path para permitir importações de 'modules'
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.utils import (
    calcula_seculo,
    int_to_roman,
    write_to_csv,
    save_session,
    load_session,
    manage_sessions,
    # Outras funções de utils podem ser importadas aqui para teste
)

class TestUtils(unittest.TestCase):

    def test_calcula_seculo(self):
        self.assertEqual(calcula_seculo("1900"), "19")
        self.assertEqual(calcula_seculo("1901"), "20")
        self.assertEqual(calcula_seculo("2000"), "20")
        self.assertEqual(calcula_seculo("2023"), "21")
        self.assertEqual(calcula_seculo("1 de Janeiro de 1800"), "18")
        self.assertEqual(calcula_seculo("100 a.C."), "1 a.C.")
        self.assertEqual(calcula_seculo("1 a.C."), "1 a.C.")
        self.assertEqual(calcula_seculo("476"), "5")
        self.assertEqual(calcula_seculo("-753"), "8 a.C.") # Ano negativo como a.C.
        self.assertEqual(calcula_seculo("753 a.C."), "8 a.C.")
        self.assertEqual(calcula_seculo("Não Informado"), "Não Informado")
        self.assertEqual(calcula_seculo(""), "Não Informado")
        self.assertEqual(calcula_seculo("texto aleatorio"), "Não Informado")
        self.assertEqual(calcula_seculo("Ano 50 DC"), "1")
        self.assertEqual(calcula_seculo("50"), "1")
        self.assertEqual(calcula_seculo("Nascimento em 25 a.C."), "1 a.C.")


    def test_int_to_roman(self):
        self.assertEqual(int_to_roman(1), "I")
        self.assertEqual(int_to_roman(4), "IV")
        self.assertEqual(int_to_roman(9), "IX")
        self.assertEqual(int_to_roman(58), "LVIII")
        self.assertEqual(int_to_roman(1994), "MCMXCIV")
        self.assertEqual(int_to_roman(3999), "MMMCMXCIX")
        with self.assertRaises(TypeError):
            int_to_roman("a")
        with self.assertRaises(ValueError):
            int_to_roman(0)
        with self.assertRaises(ValueError):
            int_to_roman(4000)

    def setUp(self):
        # Cria arquivos temporários para testes de CSV e JSON
        self.test_csv_file = "test_person_info.csv"
        self.test_sessions_dir = "test_sessions_data"
        os.makedirs(self.test_sessions_dir, exist_ok=True)

        # Limpa o arquivo de teste CSV antes de cada teste que o usa
        if os.path.exists(self.test_csv_file):
            os.remove(self.test_csv_file)

    def tearDown(self):
        # Remove arquivos e diretórios temporários após os testes
        if os.path.exists(self.test_csv_file):
            os.remove(self.test_csv_file)
        if os.path.exists(self.test_sessions_dir):
            # Remove todos os arquivos dentro do diretório de sessões de teste
            for f in os.listdir(self.test_sessions_dir):
                os.remove(os.path.join(self.test_sessions_dir, f))
            os.rmdir(self.test_sessions_dir)

    def test_write_to_csv_new_file(self):
        person_info = {"Nome Completo": "Teste Novo", "Século": "20"}
        write_to_csv(person_info, self.test_csv_file)
        self.assertTrue(os.path.exists(self.test_csv_file))
        with open(self.test_csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            self.assertEqual(reader.fieldnames, ["Nome Completo", "Século"])
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["Nome Completo"], "Teste Novo")

    def test_write_to_csv_existing_file_no_duplicate(self):
        # Escreve o primeiro registro
        person_info1 = {"Nome Completo": "Teste Existente1", "Século": "19"}
        write_to_csv(person_info1, self.test_csv_file)
        # Escreve o segundo registro (diferente)
        person_info2 = {"Nome Completo": "Teste Existente2", "Século": "20"}
        write_to_csv(person_info2, self.test_csv_file)

        with open(self.test_csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)

    def test_write_to_csv_duplicate_entry(self):
        person_info = {"Nome Completo": "Teste Duplicado", "Século": "21"}
        # Para este teste, precisamos garantir que o nome do arquivo seja "person_info.csv"
        # ou que a lógica de write_to_csv seja ajustada para testes.
        # Temporariamente, vamos usar o nome de arquivo padrão para o qual a verificação de duplicata é aplicada.
        target_csv_file = "person_info.csv"
        if os.path.exists(target_csv_file): # Limpa se já existir de execuções anteriores
            os.remove(target_csv_file)

        write_to_csv(person_info, target_csv_file) # Primeira escrita
        write_to_csv(person_info, target_csv_file) # Tentativa de duplicata

        with open(target_csv_file, 'r', newline='') as f:
            reader = list(csv.DictReader(f))
            self.assertEqual(len(reader), 1, "A entrada duplicada não deveria ter sido escrita.")

        if os.path.exists(target_csv_file): # Limpa após o teste
            os.remove(target_csv_file)


    @patch('modules.utils.shutil.copyfile')
    @patch('modules.utils.csv.DictReader')
    @patch('modules.utils.json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_session(self, mock_file_open, mock_json_dump, mock_csv_reader, mock_shutil_copy):
        # Prepara o current_data_file (person_info.csv) para ser "existente"
        # Não precisamos realmente criar o arquivo, apenas mockar os acessos a ele.

        # Mock para a leitura do CSV de origem (current_data_file)
        mock_csv_data = [{'Nome Completo': 'Marie Curie', 'Século': '20'}]
        mock_csv_reader.return_value = mock_csv_data # Retorna a lista de dicts

        # Simula que o arquivo de dados atual existe e tem conteúdo
        with patch('os.path.exists') as mock_os_exists, \
             patch('os.path.getsize') as mock_os_getsize:
            mock_os_exists.return_value = True # current_data_file existe
            mock_os_getsize.return_value = 100 # current_data_file não está vazio

            with patch('builtins.input', return_value="teste_sessao"):
                save_session(self.test_sessions_dir, current_data_file="dummy_person_info.csv")

        # Verifica se shutil.copyfile foi chamado para o CSV
        expected_csv_path = os.path.join(self.test_sessions_dir, "teste_sessao.csv")
        mock_shutil_copy.assert_called_once_with("dummy_person_info.csv", expected_csv_path)

        # Verifica se json.dump foi chamado para o JSON
        expected_json_path = os.path.join(self.test_sessions_dir, "teste_sessao.json")
        # A mock_file_open terá sido chamada múltiplas vezes. A última deve ser para o arquivo JSON.
        # Verifica a chamada para abrir o arquivo JSON para escrita
        mock_file_open.assert_any_call(expected_json_path, 'w', encoding='utf-8')

        # Verifica se json.dump foi chamado com os dados corretos
        # O primeiro argumento de mock_json_dump.call_args[0] é a lista de dados
        # O segundo argumento é o file handle mockado
        self.assertEqual(mock_json_dump.call_args[0][0], mock_csv_data)


    @patch('builtins.input', side_effect=['1', '0']) # Escolhe a primeira sessão, depois 0 para sair
    @patch('os.listdir')
    @patch('os.path.isfile')
    def test_load_session_select_and_exit(self, mock_isfile, mock_listdir, mock_input_load):
        mock_listdir.return_value = ['sessao1.csv', 'sessao1.json', 'sessao2.csv']
        mock_isfile.return_value = True

        selected_file = load_session(self.test_sessions_dir)
        self.assertEqual(selected_file, 'sessao1.csv')

        selected_file_exit = load_session(self.test_sessions_dir)
        self.assertIsNone(selected_file_exit, "Deveria retornar None ao escolher sair (0).")


    @patch('modules.utils.save_session')
    def test_manage_sessions_save(self, mock_save_session):
        manage_sessions(self.test_sessions_dir, action="save")
        mock_save_session.assert_called_once_with(self.test_sessions_dir, current_data_file="person_info.csv")

    @patch('modules.utils.load_session')
    def test_manage_sessions_load(self, mock_load_session):
        manage_sessions(self.test_sessions_dir, action="load")
        mock_load_session.assert_called_once_with(self.test_sessions_dir)


if __name__ == '__main__':
    unittest.main()
