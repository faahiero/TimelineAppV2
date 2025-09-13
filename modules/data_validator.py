"""
Sistema de validação e sanitização de dados
"""
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class DataValidator:
    """Classe para validação e sanitização de dados de personalidades"""
    
    @staticmethod
    def validate_coordinates(lat: str, lon: str) -> tuple[bool, Optional[tuple[float, float]]]:
        """Valida coordenadas geográficas"""
        try:
            lat_float = float(lat.strip())
            lon_float = float(lon.strip())
            
            # Verifica se estão dentro dos limites válidos
            if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
                return True, (lat_float, lon_float)
            else:
                return False, None
        except (ValueError, AttributeError):
            return False, None
    
    @staticmethod
    def validate_date(date_str: str) -> tuple[bool, Optional[str]]:
        """Valida e normaliza datas"""
        if not date_str or date_str.strip() in ["", "Não Informado", "-"]:
            return True, "Não Informado"
        
        date_str = date_str.strip()
        
        # Padrões de data suportados
        patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # ISO: 2023-12-25
            r'^\d{1,2} de \w+ de \d{4}$',  # Brasileiro: 25 de dezembro de 2023
            r'^\d{4}$',  # Apenas ano: 2023
            r'^\d{4} a\.C\.$',  # Ano a.C.: 500 a.C.
        ]
        
        for pattern in patterns:
            if re.match(pattern, date_str):
                return True, date_str
        
        # Tenta extrair pelo menos o ano
        year_match = re.search(r'\b(\d{4})\b', date_str)
        if year_match:
            return True, year_match.group(1)
        
        return False, None
    
    @staticmethod
    def validate_name(name: str) -> tuple[bool, Optional[str]]:
        """Valida e sanitiza nomes"""
        if not name or not name.strip():
            return False, None
        
        name = name.strip()
        
        # Remove caracteres especiais excessivos
        name = re.sub(r'[^\w\s\-\.\,\(\)\'\"àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]', '', name)
        
        # Verifica se tem pelo menos 2 caracteres
        if len(name) < 2:
            return False, None
        
        # Verifica se não é apenas números
        if name.isdigit():
            return False, None
        
        return True, name
    
    @staticmethod
    def validate_url(url: str) -> tuple[bool, Optional[str]]:
        """Valida URLs"""
        if not url or not url.strip():
            return True, "Não Informado"
        
        url = url.strip()
        
        # Padrão básico de URL
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        
        if re.match(url_pattern, url):
            return True, url
        
        return False, None
    
    @staticmethod
    def sanitize_person_data(person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza todos os dados de uma pessoa"""
        sanitized = {}
        
        # Validação do nome
        is_valid, clean_name = DataValidator.validate_name(
            person_data.get("Nome Completo", "")
        )
        if not is_valid:
            raise ValueError("Nome inválido")
        sanitized["Nome Completo"] = clean_name
        
        # Validação de coordenadas
        lat = person_data.get("Latitude", "")
        lon = person_data.get("Longitude", "")
        is_valid, coords = DataValidator.validate_coordinates(lat, lon)
        if is_valid and coords:
            sanitized["Latitude"] = coords[0]
            sanitized["Longitude"] = coords[1]
        else:
            sanitized["Latitude"] = "Não Informado"
            sanitized["Longitude"] = "Não Informado"
        
        # Validação de datas
        for date_field in ["Data de Nascimento", "Data de Falecimento"]:
            is_valid, clean_date = DataValidator.validate_date(
                person_data.get(date_field, "")
            )
            sanitized[date_field] = clean_date if is_valid else "Não Informado"
        
        # Validação de URL
        is_valid, clean_url = DataValidator.validate_url(
            person_data.get("Url", "")
        )
        sanitized["Url"] = clean_url if is_valid else "Não Informado"
        
        # Campos de texto simples
        text_fields = [
            "Termo Buscado", "Origem/Nacionalidade", 
            "Local de Nascimento", "Local de Falecimento", 
            "Século", "Imagem"
        ]
        
        for field in text_fields:
            value = person_data.get(field, "")
            if isinstance(value, str) and value.strip():
                sanitized[field] = value.strip()
            else:
                sanitized[field] = "Não Informado"
        
        return sanitized
    
    @staticmethod
    def validate_csv_data(csv_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Valida dados de um CSV inteiro"""
        validated_data = []
        errors = []
        
        for i, person_data in enumerate(csv_data):
            try:
                sanitized = DataValidator.sanitize_person_data(person_data)
                validated_data.append(sanitized)
            except Exception as e:
                errors.append(f"Linha {i+1}: {str(e)}")
        
        if errors:
            print(f"Encontrados {len(errors)} erros na validação:")
            for error in errors[:5]:  # Mostra apenas os primeiros 5
                print(f"  - {error}")
            if len(errors) > 5:
                print(f"  ... e mais {len(errors) - 5} erros")
        
        return validated_data

# Instância global do validador
validator = DataValidator()