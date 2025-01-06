import os
import json
import csv
from lxml import etree
import ifcopenshell
import pyproj

# Defina o caminho para o arquivo IDS e para o relatório
IDS_PATH = "./ids.xsd"
REPORT_PATH = "reports/validation_report.json"  # Caminho do relatório JSON

# Defina os campos adicionais que você deseja verificar
additional_fields = [
    "IfcWall", "IfcSlab", "IfcWindow", "IfcDoor", "IfcBeam", "IfcColumn", 
    "IfcRailing", "IfcStair", "IfcRoof"
]

# Função para validar a presença dos campos no arquivo IFC
def validate_ifc_with_ids(file, ids_root):
    try:
        # Carrega o arquivo IFC
        ifc_file = ifcopenshell.open(file)
        
        # Extração de dados do arquivo IFC
        project = ifc_file.by_type("IfcProject")
        building = ifc_file.by_type("IfcBuilding")
        building_storey = ifc_file.by_type("IfcBuildingStorey")
        spaces = ifc_file.by_type("IfcSpace")
        coordinates = get_coordinates(ifc_file)
        
        # Obtendo os valores dos campos adicionais
        additional_data = {}
        for field in additional_fields:
            additional_data[field] = len(ifc_file.by_type(field))

        # Simulando um retorno de disciplinas e especificações técnicas
        disciplines = "Nenhuma disciplina encontrada"
        technical_specifications = "Ausentes"
        
        # Criando o resultado da validação
        result = {
            "file": file,
            "results": [{
                "IfcProject": "Presente" if project else "Ausente",
                "IfcBuilding": "Presente" if building else "Ausente",
                "IfcBuildingStorey": "Presente" if building_storey else "Ausente",
                "IfcSpace": f"{len(spaces)} espaços encontrados" if spaces else "Ausente",
                "Coordenadas": coordinates,
                "Disciplinas": disciplines,
                "Especificações Técnicas": technical_specifications
            }]
        }
        
        # Adiciona os campos adicionais ao resultado
        for field, count in additional_data.items():
            result["results"][0][field] = f"{count} encontrados" if count > 0 else "Ausente"
        
        return result
    except Exception as e:
        return {
            "file": file,
            "error": str(e)
        }

# Função para obter as coordenadas geográficas do projeto
def get_coordinates(ifc_file):
    # Usando um projecionista geográfico para converter as coordenadas
    coord_transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    
    # Buscando os dados de coordenadas (usualmente o IfcSite tem as coordenadas)
    ifc_site = ifc_file.by_type("IfcSite")
    if ifc_site:
        site = ifc_site[0]
        if hasattr(site, "RefLatitude") and hasattr(site, "RefLongitude"):
            lat = site.RefLatitude
            lon = site.RefLongitude
            elevation = getattr(site, "RefElevation", "0.0")
            lat_lon = coord_transformer.transform(lon, lat)
            return f"Latitude: {lat}, Longitude: {lon}, Elevation: {elevation}m"
    return "Coordenadas não encontradas"

def main():
    # Verificar se o diretório de relatórios existe; caso contrário, criá-lo
    if not os.path.exists("reports"):
        os.makedirs("reports")
    # Carrega o IDS
    with open(IDS_PATH, "r") as f:
        ids_root = etree.parse(f).getroot()

    # Valida todos os arquivos IFC no repositório
    validation_reports = []
    for file in os.listdir("."):
        if file.endswith(".ifc"):
            validation_reports.append(validate_ifc_with_ids(file, ids_root))

    # Salva o relatório completo em formato JSON
    with open(REPORT_PATH, "w") as report_file:
        json.dump(validation_reports, report_file, indent=4)

    # Salva o relatório completo em formato TXT
    with open("validation_report.txt", "w") as txt_file:
        for report in validation_reports:
            txt_file.write(f"Arquivo: {report['file']}\n")
            if "error" in report:
                txt_file.write(f"  Erro: {report['error']}\n")
            else:
                for result in report["results"]:
                    txt_file.write(f"  IfcProject: {result.get('IfcProject', 'N/A')}\n")
                    txt_file.write(f"  IfcBuilding: {result.get('IfcBuilding', 'N/A')}\n")
                    txt_file.write(f"  IfcBuildingStorey: {result.get('IfcBuildingStorey', 'N/A')}\n")
                    txt_file.write(f"  IfcSpace: {result.get('IfcSpace', 'N/A')}\n")
                    txt_file.write(f"  Coordenadas: {result.get('Coordenadas', 'N/A')}\n")
                    txt_file.write(f"  Disciplinas: {result.get('Disciplinas', 'N/A')}\n")
                    txt_file.write(f"  Especificações Técnicas: {result.get('Especificações Técnicas', 'N/A')}\n")
                    # Loop para os novos campos Ifc
                    for field in additional_fields:
                        txt_file.write(f"  {field}: {result.get(field, 'Ausente')}\n")
            txt_file.write("\n")

    # Salva o relatório completo em formato CSV
    with open("validation_report.csv", "w", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        # Cabeçalhos do CSV
        headers = [
            "Arquivo", "IfcProject", "IfcBuilding", "IfcBuildingStorey", "IfcSpace",
            "Coordenadas", "Disciplinas", "Especificações Técnicas"
        ] + additional_fields
        csv_writer.writerow(headers)

        # Escreve os dados
        for report in validation_reports:
            if "error" in report:
                csv_writer.writerow([report["file"], report["error"]] + [""] * (len(headers) - 2))
            else:
                for result in report["results"]:
                    row = [
                        report["file"],
                        result.get("IfcProject", "N/A"),
                        result.get("IfcBuilding", "N/A"),
                        result.get("IfcBuildingStorey", "N/A"),
                        result.get("IfcSpace", "N/A"),
                        result.get("Coordenadas", "N/A"),
                        result.get("Disciplinas", "N/A"),
                        result.get("Especificações Técnicas", "N/A")
                    ]
                    row.extend(result.get(field, "Ausente") for field in additional_fields)
                    csv_writer.writerow(row)

if __name__ == "__main__":
    main()

print(f"Diretório atual: {os.getcwd()}")
